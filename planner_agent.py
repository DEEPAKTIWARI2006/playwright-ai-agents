import asyncio
import json
import re
from pathlib import Path

from docx import Document
from dotenv import load_dotenv
import os

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from langchain_ollama import OllamaLLM

# ---------------------------------------------------------------------
# Configuration: loaded from .env
# ---------------------------------------------------------------------

# Load .env from the same directory as this script, regardless of the
# directory from which the script is launched.
SCRIPT_DIR = Path(__file__).resolve().parent
load_dotenv(SCRIPT_DIR / ".env")


def env_path(name: str, default: str) -> Path:
    """Resolve a path from .env; relative paths are relative to the project cwd."""
    return Path(os.getenv(name, default)).expanduser()


CONFIG_FILE = env_path("PLANNER_MCP_CONFIG_FILE", "playwright_mcp_config.json")
REQUIREMENTS_FILE = env_path(
    "PLANNER_REQUIREMENTS_FILE",
    "requirements/SauceDemo_Requirements_Specification.docx",
)
PLANNER_INSTRUCTIONS_FILE = env_path(
    "PLANNER_INSTRUCTIONS_FILE",
    "playwright-mcp-skills/playwright-test-planner.agent.md",
)
ARTIFACTS_DIR = env_path("PLANNER_ARTIFACTS_DIR", "artifacts")
TEST_PLAN_OUTPUT_FILE = env_path(
    "PLANNER_TEST_PLAN_OUTPUT_FILE", "artifacts/test_plan.md"
)
TEST_CASES_OUTPUT_FILE = env_path(
    "PLANNER_TEST_CASES_OUTPUT_FILE", "artifacts/test_cases.json"
)
RAW_RESPONSE_OUTPUT_FILE = env_path(
    "PLANNER_RAW_RESPONSE_OUTPUT_FILE", "artifacts/test_generation_raw_response.txt"
)
BASE_URL = os.getenv("PLANNER_BASE_URL", "https://www.saucedemo.com/")
MODEL_NAME = os.getenv("PLANNER_MODEL_NAME", "gemma4:31b-cloud")
MAX_EXPLORATION_ACTIONS = int(os.getenv("PLANNER_MAX_EXPLORATION_ACTIONS", "25"))

ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
for output_path in (
    TEST_PLAN_OUTPUT_FILE,
    TEST_CASES_OUTPUT_FILE,
    RAW_RESPONSE_OUTPUT_FILE,
):
    output_path.parent.mkdir(parents=True, exist_ok=True)

with CONFIG_FILE.open("r", encoding="utf-8") as file:
    MCP_CONFIG = json.load(file)

llm = OllamaLLM(model=MODEL_NAME)


# ---------------------------------------------------------------------
# Load the work already completed. Do not regenerate these artifacts.
# ---------------------------------------------------------------------


def read_requirements_document():
    """Read paragraphs and tables directly from the source requirements DOCX."""
    if not REQUIREMENTS_FILE.exists():
        raise FileNotFoundError(
            f"Requirements document not found: {REQUIREMENTS_FILE.resolve()}"
        )

    document = Document(REQUIREMENTS_FILE)
    sections = []

    for paragraph in document.paragraphs:
        value = paragraph.text.strip()
        if value:
            sections.append(value)

    for table_index, table in enumerate(document.tables, start=1):
        sections.append(f"\nTABLE {table_index}")
        for row in table.rows:
            cells = [cell.text.strip().replace("\n", " ") for cell in row.cells]
            sections.append(" | ".join(cells))

    content = "\n".join(sections).strip()
    if not content:
        raise ValueError(
            f"Requirements document is empty: {REQUIREMENTS_FILE.resolve()}"
        )

    print(f"Extracted {len(content)} characters from the requirements DOCX.")
    return content


def load_planner_inputs():
    """Load the source DOCX and optional planner instructions only."""
    loaded = {"requirements_document": read_requirements_document()}
    print(f"Loaded requirements_document: {REQUIREMENTS_FILE}")

    # The skill file is optional. The planner has built-in instructions below,
    # so this file is not required to run the agent.
    if PLANNER_INSTRUCTIONS_FILE.exists():
        loaded["planner_instructions"] = PLANNER_INSTRUCTIONS_FILE.read_text(
            encoding="utf-8"
        ).strip()
        print(f"Loaded planner_instructions: {PLANNER_INSTRUCTIONS_FILE}")
    else:
        loaded["planner_instructions"] = (
            "Follow the source requirements strictly. Preserve requirement IDs, "
            "do not invent expected behavior, and use browser evidence to "
            "distinguish observed behavior from unverified requirements."
        )
        print("Planner skill file not found; using built-in instructions.")

    return loaded


def parse_json_response(response_text):
    """Parse JSON returned by the LLM, including a fenced JSON response."""
    text = str(response_text).strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    return json.loads(text)


def extract_text(tool_result):
    return "\n".join(item.text for item in tool_result.content if hasattr(item, "text"))


# ---------------------------------------------------------------------
# Planner: explore SauceDemo with the available Playwright MCP tools.
# ---------------------------------------------------------------------


async def explore_application(session, available_tools, inputs):
    tool_names = [
        tool.name
        for tool in available_tools
        if tool.name.startswith("browser_") and tool.name != "browser_run_code_unsafe"
    ]

    print("\nAvailable browser tools for the Planner:")
    print(", ".join(tool_names))

    # Start at the target application and inspect its initial state.
    navigation = await session.call_tool(
        "browser_navigate", arguments={"url": BASE_URL}
    )
    initial_snapshot = await session.call_tool("browser_snapshot", arguments={})

    navigation_text = extract_text(navigation)
    snapshot_text = extract_text(initial_snapshot)

    evidence = [
        {
            "step": 0,
            "requirement_id": "Initial application inspection",
            "action": "browser_navigate",
            "arguments": {"url": BASE_URL},
            "result": navigation_text,
            "snapshot": snapshot_text,
        }
    ]

    print("\nInitial SauceDemo snapshot:")
    print(snapshot_text[:5000])

    prompt = f"""
You are the Planner Agent for SauceDemo. Explore the application directly
from the source requirements DOCX. Do not depend on pre-generated scope,
scope-review, proposed-activities, or requirements-analysis files. Derive a
concise exploration scope and approved activities from the requirements at
runtime.

## Planner skill instructions
{inputs["planner_instructions"]}

## Source requirements specification (extracted from DOCX)
{inputs["requirements_document"]}

## Available browser tools
{json.dumps(tool_names, indent=2)}

## Your task
First derive the relevant exploration activities from the requirements.
Only explore behavior covered by the requirements. Use browser tools to
inspect the real application. Prefer browser_snapshot over screenshots.
Keep track of requirement IDs, actions, observed UI, and evidence. Do not
invent observed behavior. Cover relevant positive, negative, validation,
boundary, cart, and checkout flows where supported by the requirements.
Do not navigate outside the target SauceDemo application or perform actions
that are unrelated to the requirements. Treat non-UI requirements as gaps
when they cannot be verified through browser exploration.

For each turn, return exactly one JSON object, without Markdown fences.

To request a browser action:
{{
  "done": false,
  "requirement_id": "a requirement ID from the supplied inputs",
  "activity": "the activity being explored",
  "tool": "one of the available browser tools",
  "arguments": {{}},
  "reason": "brief reason for the action"
}}

When exploration is complete, return:
{{
  "done": true,
  "summary": "brief summary of what was explored"
}}

Do not return a final test plan until exploration is complete.
"""

    action_count = 0
    while action_count < MAX_EXPLORATION_ACTIONS:
        current_evidence = evidence[-1]
        turn_prompt = (
            prompt
            + "\n\n## Latest browser snapshot\n"
            + current_evidence.get("snapshot", "")
            + "\n\n## Latest browser action result\n"
            + current_evidence.get("result", "")
            + "\n\n## Exploration evidence so far\n"
            + json.dumps(evidence, ensure_ascii=False, indent=2)[-18000:]
            + "\n\nChoose the next action or mark exploration done."
        )

        response = llm.invoke(turn_prompt)
        try:
            action = parse_json_response(response)
        except (json.JSONDecodeError, TypeError) as exc:
            print("\nCould not parse Gemma's action response. Stopping exploration.")
            print(response)
            print(f"Parsing error: {exc}")
            break

        if action.get("done") is True:
            print("\nPlanner exploration summary:")
            print(action.get("summary", "No summary supplied."))
            break

        tool_name = action.get("tool")
        arguments = action.get("arguments", {})

        if tool_name not in tool_names:
            print(f"\nPlanner requested an unavailable tool: {tool_name}")
            print("Stopping exploration. Check the model response and tool list.")
            break

        if not isinstance(arguments, dict):
            print("\nPlanner returned invalid tool arguments. Stopping exploration.")
            break

        requirement_id = action.get("requirement_id", "Requirement not specified")
        activity = action.get("activity", "Activity not specified")
        reason = action.get("reason", "")

        print(
            f"\n[{action_count + 1}/{MAX_EXPLORATION_ACTIONS}] "
            f"{requirement_id} | {tool_name}\n{reason}"
        )

        try:
            result = await session.call_tool(tool_name, arguments=arguments)
            result_text = extract_text(result)

            # Capture the resulting page state after every browser action.
            snapshot_result = await session.call_tool("browser_snapshot", arguments={})
            new_snapshot = extract_text(snapshot_result)
        except Exception as exc:
            result_text = f"Tool call failed: {type(exc).__name__}: {exc}"
            new_snapshot = current_evidence.get("snapshot", "")
            print(result_text)

        evidence.append(
            {
                "step": action_count + 1,
                "requirement_id": requirement_id,
                "activity": activity,
                "action": tool_name,
                "arguments": arguments,
                "reason": reason,
                "result": result_text,
                "snapshot": new_snapshot,
            }
        )
        action_count += 1

    if action_count >= MAX_EXPLORATION_ACTIONS:
        print(f"\nReached the {MAX_EXPLORATION_ACTIONS}-action exploration limit.")

    return evidence


# ---------------------------------------------------------------------
# Convert requirements + browser evidence into Generator-ready test cases.
# ---------------------------------------------------------------------


def generate_test_artifacts(inputs, evidence):
    prompt = f"""
You are a senior QA test planner. Create a complete test plan and a
Generator-ready JSON test cases file using the source requirements specification and
the actual exploration evidence.

## Source requirements specification (extracted from DOCX)
{inputs["requirements_document"]}

## Actual exploration evidence
{json.dumps(evidence, ensure_ascii=False, indent=2)}

Rules:
- Treat the source requirements specification as the authoritative baseline.
- Preserve requirement IDs and documented expected behavior.
- Use the observed UI evidence for page names, labels, and interactions.
- Do not claim a UI behavior was observed unless evidence supports it.
- Cover requirements with positive, negative, validation, boundary, and
  end-to-end scenarios where applicable.
- If a requirement was not explored or cannot be verified, identify the
  gap; do not fabricate observations.
- Each test case must be independent and have clear preconditions,
  numbered steps, and expected results.
- Include test_case_id, requirement_id, title, priority, preconditions,
  steps, expected_results, observations, and status.
- Return valid JSON for the test cases.
- The Markdown plan must be comprehensive and traceable to requirements.

Return exactly one JSON object in this structure:
{{
  "test_plan_markdown": "complete Markdown test plan as a JSON string",
  "test_cases": [
    {{
      "test_case_id": "TC-AUTH-001",
      "requirement_id": "REQ-AUTH-001",
      "title": "Descriptive title",
      "priority": "P1",
      "preconditions": [],
      "steps": [
        {{
          "step": 1,
          "action": "user action",
          "expected_result": "expected result"
        }}
      ],
      "expected_results": [],
      "observations": [],
      "status": "ready_for_generation"
    }}
  ]
}}
Do not put Markdown fences around the JSON.
"""

    print("\nGemma is generating the test plan and test cases...")
    response = llm.invoke(prompt)

    try:
        output = parse_json_response(response)
    except (json.JSONDecodeError, TypeError) as exc:
        raw_file = RAW_RESPONSE_OUTPUT_FILE
        raw_file.write_text(str(response), encoding="utf-8")
        raise ValueError(
            "Gemma did not return valid JSON. Raw response saved to "
            f"{raw_file.resolve()}. Parsing error: {exc}"
        ) from exc

    test_plan = output.get("test_plan_markdown", "")
    test_cases = output.get("test_cases", [])

    if not isinstance(test_plan, str) or not isinstance(test_cases, list):
        raise ValueError(
            "Gemma's output did not contain the expected plan and test cases."
        )

    plan_file = TEST_PLAN_OUTPUT_FILE
    plan_file.write_text(test_plan, encoding="utf-8")

    cases_file = TEST_CASES_OUTPUT_FILE
    cases_file.write_text(
        json.dumps(test_cases, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"\nTest plan saved to: {plan_file.resolve()}")
    print(f"Test cases saved to: {cases_file.resolve()}")
    print(f"Test cases generated: {len(test_cases)}")


async def main():
    inputs = load_planner_inputs()

    server_params = StdioServerParameters(
        command=MCP_CONFIG["command"],
        args=MCP_CONFIG["args"],
    )

    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            tool_response = await session.list_tools()

            evidence = await explore_application(
                session,
                tool_response.tools,
                inputs,
            )

    # Generate the plan and JSON after the browser session closes.
    generate_test_artifacts(inputs, evidence)


if __name__ == "__main__":
    asyncio.run(main())
