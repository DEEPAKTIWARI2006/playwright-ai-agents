import asyncio
import json
import re
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from langchain_ollama import OllamaLLM

PROJECT_ROOT = Path(__file__).resolve().parent
ARTIFACTS_DIR = PROJECT_ROOT / "artifacts"
SKILLS_DIR = PROJECT_ROOT / "playwright-mcp-skills"

TEST_PLAN_FILE = ARTIFACTS_DIR / "test_plan.md"
TEST_CASES_FILE = ARTIFACTS_DIR / "test_cases.json"
GENERATOR_INSTRUCTIONS_FILE = SKILLS_DIR / "playwright-test-generator.agent.md"
MCP_CONFIG_FILE = PROJECT_ROOT / "playwright_mcp_config.json"

OUTPUT_DIR = PROJECT_ROOT / "generated-tests"
BASE_URL = "https://www.saucedemo.com/"

llm = OllamaLLM(model="gemma4:31b-cloud")


def load_generator_inputs():
    required_files = [
        TEST_PLAN_FILE,
        TEST_CASES_FILE,
        GENERATOR_INSTRUCTIONS_FILE,
        MCP_CONFIG_FILE,
    ]
    for file_path in required_files:
        if not file_path.is_file():
            raise FileNotFoundError(f"Required file not found: {file_path}")

    test_plan = TEST_PLAN_FILE.read_text(encoding="utf-8")
    with TEST_CASES_FILE.open("r", encoding="utf-8") as file:
        test_cases = json.load(file)
    instructions = GENERATOR_INSTRUCTIONS_FILE.read_text(encoding="utf-8")
    with MCP_CONFIG_FILE.open("r", encoding="utf-8") as file:
        mcp_config = json.load(file)

    print("Generator inputs loaded.")
    print(f"Test plan: {TEST_PLAN_FILE}")
    print(f"Test cases: {TEST_CASES_FILE}")
    print(f"Instructions: {GENERATOR_INSTRUCTIONS_FILE}")
    return test_plan, test_cases, instructions, mcp_config


def extract_test_cases(data):
    """Support common JSON shapes without assuming one exact wrapper key."""
    if isinstance(data, list):
        cases = data
    elif isinstance(data, dict):
        cases = None
        for key in ("test_cases", "testCases", "tests", "scenarios", "cases"):
            value = data.get(key)
            if isinstance(value, list):
                cases = value
                break
        if cases is None:
            if any(key in data for key in ("test_name", "title", "name", "scenario")):
                cases = [data]
            else:
                raise ValueError(
                    "Could not find a list of test cases in test_cases.json. "
                    "Expected a top-level list or a list under test_cases/tests/scenarios."
                )
    else:
        raise ValueError("test_cases.json must contain a JSON object or array.")

    if not cases:
        raise ValueError("test_cases.json contains no test cases.")
    return cases


def case_title(case, index):
    if isinstance(case, dict):
        for key in ("test_name", "title", "name", "scenario", "test_case", "id"):
            value = case.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
    return f"Generated scenario {index}"


def safe_file_name(title):
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", title.strip()).strip("-").lower()
    return f"{slug or 'generated-test'}.spec.ts"


def strip_code_fences(text):
    text = (text or "").strip()
    if text.startswith("```"):
        lines = text.splitlines()
        lines = lines[1:] if lines else []
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    return text


async def capture_page_snapshot(session):
    print(f"\nNavigating to {BASE_URL}")
    navigation = await session.call_tool(
        "browser_navigate",
        arguments={"url": BASE_URL},
    )
    if getattr(navigation, "isError", False):
        details = "\n".join(
            item.text for item in navigation.content if hasattr(item, "text")
        )
        raise RuntimeError(f"Playwright MCP navigation failed:\n{details}")

    snapshot_result = await session.call_tool("browser_snapshot", arguments={})
    if getattr(snapshot_result, "isError", False):
        details = "\n".join(
            item.text for item in snapshot_result.content if hasattr(item, "text")
        )
        raise RuntimeError(f"Playwright MCP snapshot failed:\n{details}")

    snapshot_text = "\n".join(
        item.text
        for item in snapshot_result.content
        if hasattr(item, "text") and item.text
    )
    if not snapshot_text.strip():
        raise RuntimeError("Playwright MCP returned an empty page snapshot.")

    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    snapshot_file = ARTIFACTS_DIR / "generator_page_snapshot.txt"
    snapshot_file.write_text(snapshot_text, encoding="utf-8")
    print(f"Snapshot saved: {snapshot_file}")
    print(f"Snapshot length: {len(snapshot_text):,} characters")
    return snapshot_text


def build_case_prompt(test_plan, case, instructions, snapshot, index, total):
    return f"""
You are generating one Playwright Test test file in TypeScript.

Follow these instructions from playwright-test-generator.agent.md:
{instructions}

Relevant test plan:
{test_plan}

Test case {index} of {total} (JSON):
{json.dumps(case, ensure_ascii=False, indent=2)}

Observed SauceDemo page accessibility snapshot:
{snapshot}

Requirements:
- Generate ONLY the complete TypeScript source code for this single test case.
- Do not return JSON, Markdown explanations, or multiple alternatives.
- Use Playwright Test imports and a standard test.describe/test structure.
- Keep the test title aligned with the supplied scenario.
- Include a comment matching each test step before its corresponding action.
- Add assertions for the expected results in the test case.
- Ground locators in the supplied snapshot when possible. Do not claim that the snapshot proves elements on pages that have not been visited.
- For interactions on pages not represented by this snapshot, use accessible locators only when justified by the scenario; otherwise add a clear TODO comment rather than claiming the locator was verified.
- Do not import project-specific fixtures or page objects; generate standalone Playwright Test scripts.
- Output source code only. A single TypeScript code fence is acceptable.
"""


async def generate_one_test(test_plan, case, instructions, snapshot, index, total):
    title = case_title(case, index)
    prompt_text = build_case_prompt(
        test_plan, case, instructions, snapshot, index, total
    )
    print(f"\nGenerating {index}/{total}: {title}")
    print(f"Prompt length: {len(prompt_text):,} characters")

    response_text = await asyncio.to_thread(llm.invoke, prompt_text)
    source_code = strip_code_fences(response_text)
    if not source_code:
        raise ValueError(
            f"Ollama returned an empty response for scenario {index}: {title}. "
            f"Prompt length was {len(prompt_text):,} characters."
        )

    if not any(token in source_code for token in ("test(", "test.describe", "test (")):
        print("Warning: response may not contain a complete Playwright test.")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_file = OUTPUT_DIR / safe_file_name(title)
    if output_file.exists():
        output_file = OUTPUT_DIR / f"{index:02d}-{output_file.name}"

    output_file.write_text(source_code.rstrip() + "\n", encoding="utf-8")
    print(f"Saved: {output_file}")
    return output_file


async def main():
    test_plan, raw_test_cases, instructions, mcp_config = load_generator_inputs()
    cases = extract_test_cases(raw_test_cases)
    print(f"Found {len(cases)} test case(s).")

    server_params = StdioServerParameters(
        command=mcp_config["command"],
        args=mcp_config["args"],
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools_response = await session.list_tools()
            tool_names = [tool.name for tool in tools_response.tools]

            # print("\nMCP connection established. Available tools:")
            # for name in tool_names:
            #     print(f"- {name}")

            # required_tools = {"browser_navigate", "browser_snapshot"}
            # missing_tools = required_tools.difference(tool_names)
            # if missing_tools:
            #     raise RuntimeError(
            #         "MCP server is missing required tool(s): "
            #         + ", ".join(sorted(missing_tools))
            #     )

            snapshot = await capture_page_snapshot(session)

    # One focused LLM request per scenario avoids one enormous JSON response.
    generated_files = []
    for index, case in enumerate(cases, start=1):
        output_file = await generate_one_test(
            test_plan, case, instructions, snapshot, index, len(cases)
        )
        generated_files.append(output_file)

    print(f"\nGeneration complete. Created {len(generated_files)} file(s):")
    for path in generated_files:
        print(f"- {path}")


if __name__ == "__main__":
    asyncio.run(main())
