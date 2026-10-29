import asyncio
import json
import re
import shutil
import sys
import tempfile
from pathlib import Path

from langchain.agents import create_agent
from langchain.tools import tool
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_ollama import ChatOllama

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PROJECT_ROOT = Path(__file__).resolve().parent
JSON_REPORT = PROJECT_ROOT / "test-results" / "results.json"
HTML_REPORT = PROJECT_ROOT / "playwright-report" / "index.html"
ARTIFACTS_DIR = PROJECT_ROOT / "test-results"
AGENT_INSTRUCTIONS_FILE = (
    PROJECT_ROOT / "playwright-mcp-skills" / "playwright-test-healer.agent.md"
)
FAILURE_CONTEXT_FILE = PROJECT_ROOT / "artifacts" / "failure-context.json"
MODEL_NAME = "gpt-oss:120b-cloud"
FAILURE_STATUSES = {"failed", "timedOut", "interrupted"}
HEALER_TIMEOUT_SECONDS = 180
MCP_STARTUP_TIMEOUT_SECONDS = 45
PRESERVED_DIRS = ("test-results", "playwright-report")


def snapshot_preserved_artifacts() -> tuple[Path, dict[str, bool]]:
    """Snapshot report/artifact directories before MCP tools can touch them.

    The temporary snapshot is stored outside the project. It allows the healer
    to restore the exact pre-healing contents, including results.json, even if an
    MCP tool unexpectedly clears or rewrites these folders.
    """
    backup_root = Path(tempfile.mkdtemp(prefix="playwright-healer-preserve-"))
    existed: dict[str, bool] = {}
    try:
        for dirname in PRESERVED_DIRS:
            source = PROJECT_ROOT / dirname
            existed[dirname] = source.exists()
            if source.is_dir():
                shutil.copytree(source, backup_root / dirname)
            elif source.exists():
                shutil.copy2(source, backup_root / dirname)
        return backup_root, existed
    except Exception:
        shutil.rmtree(backup_root, ignore_errors=True)
        raise


def restore_preserved_artifacts(backup_root: Path, existed: dict[str, bool]) -> None:
    """Restore report/artifact folders to their exact pre-invocation state."""
    errors = []
    for dirname in PRESERVED_DIRS:
        destination = PROJECT_ROOT / dirname
        backup = backup_root / dirname
        try:
            if destination.is_dir():
                shutil.rmtree(destination)
            elif destination.exists():
                destination.unlink()

            if existed.get(dirname, False) and backup.exists():
                if backup.is_dir():
                    shutil.copytree(backup, destination)
                else:
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(backup, destination)
        except Exception as exc:
            errors.append(f"{dirname}: {exc}")
    shutil.rmtree(backup_root, ignore_errors=True)
    if errors:
        raise RuntimeError(
            "Could not fully restore preserved Playwright artifacts: " + "; ".join(errors)
        )


def load_agent_instructions() -> str:
    """Load the existing Playwright healer instructions."""
    if not AGENT_INSTRUCTIONS_FILE.is_file():
        raise FileNotFoundError(
            f"Playwright healer instructions not found: {AGENT_INSTRUCTIONS_FILE}"
        )
    return AGENT_INSTRUCTIONS_FILE.read_text(encoding="utf-8")


def clean_error(message: str) -> str:
    return re.sub(r"\x1b\[[0-9;]*m", "", message or "").strip()


def collect_failures() -> list[dict]:
    """Read Playwright's existing JSON report without changing report artifacts."""
    if not JSON_REPORT.is_file():
        raise FileNotFoundError(
            f"Playwright JSON report not found: {JSON_REPORT}\n"
            "Run your Playwright tests manually before running healer_agent.py."
        )

    with JSON_REPORT.open("r", encoding="utf-8") as file:
        report = json.load(file)

    failures = []

    def resolve_report_test_file(file_value: str) -> Path:
        """Resolve Playwright's file value to the actual original test file.

        Playwright JSON can report just a filename, a project-relative path,
        or an absolute path. The configured tests/ copy is preferred because
        that is the directory Playwright executed from in this project.
        """
        if not file_value:
            raise ValueError("Playwright report did not provide a test file path.")

        # Path() on Windows handles Windows absolute paths. The PureWindowsPath
        # check also lets us recognize Windows paths if this script is inspected
        # or run from a non-Windows environment.
        reported = Path(file_value)
        candidates = []

        if reported.is_absolute():
            candidates.append(reported)
        else:
            normalized = file_value.replace("\\", "/")
            parts = [part for part in normalized.split("/") if part and part != "."]

            # If the report gives only a filename, try the executed tests/ copy
            # first, then generated-tests/, then the project root.
            if parts and parts[0] in {"tests", "generated-tests", "healed-tests"}:
                relative = Path(*parts)
                candidates.append(PROJECT_ROOT / relative)
                if parts[0] == "healed-tests":
                    inner = Path(*parts[1:]) if len(parts) > 1 else Path()
                    candidates.extend([
                        PROJECT_ROOT / "tests" / inner,
                        PROJECT_ROOT / "generated-tests" / inner,
                    ])
            else:
                relative = Path(*parts) if parts else Path(file_value)
                candidates.extend([
                    PROJECT_ROOT / "tests" / relative,
                    PROJECT_ROOT / relative,
                    PROJECT_ROOT / "generated-tests" / relative,
                ])

        for candidate in candidates:
            resolved = candidate.resolve()
            try:
                resolved.relative_to(PROJECT_ROOT.resolve())
            except ValueError:
                continue
            if resolved.is_file() and resolved.suffix.lower() in {".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs"}:
                return resolved

        attempted = "\n".join(str(candidate) for candidate in candidates)
        raise FileNotFoundError(
            f"Could not resolve original test file from Playwright report value: {file_value}\n"
            f"Checked these paths:\n{attempted}"
        )

    def visit_suite(suite: dict, parent_file: str = "") -> None:
        suite_file = suite.get("file") or parent_file
        for spec in suite.get("specs", []):
            reported_test_file = spec.get("file") or suite_file
            test_file = str(resolve_report_test_file(reported_test_file)) if reported_test_file else ""
            title = spec.get("title", "Untitled test")
            for test in spec.get("tests", []):
                for result in test.get("results", []):
                    status = result.get("status", "")
                    if status not in FAILURE_STATUSES:
                        continue

                    error_objects = []
                    if isinstance(result.get("error"), dict):
                        error_objects.append(result["error"])
                    error_objects.extend(
                        item for item in result.get("errors", [])
                        if isinstance(item, dict)
                    )

                    errors = []
                    for error in error_objects:
                        errors.append({
                            "message": clean_error(error.get("message", "")),
                            "stack": clean_error(error.get("stack", "")),
                            "location": error.get("location"),
                        })

                    failures.append({
                        # Playwright JSON may not contain the MCP test ID.
                        "test_id": test.get("testId") or test.get("id"),
                        "title": title,
                        "file": test_file,
                        "project": test.get("projectName", ""),
                        "status": status,
                        "retry": result.get("retry", 0),
                        "errors": errors,
                        "attachments": [
                            {
                                "name": item.get("name"),
                                "content_type": item.get("contentType"),
                                "path": item.get("path"),
                            }
                            for item in result.get("attachments", [])
                        ],
                    })

        for child_suite in suite.get("suites", []):
            visit_suite(child_suite, suite_file)

    for suite in report.get("suites", []):
        visit_suite(suite)
    return failures


def write_failure_context(failures: list[dict]) -> Path:
    """Write consolidated failure data outside the Playwright report folders."""
    FAILURE_CONTEXT_FILE.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "source_report": str(JSON_REPORT),
        "html_report": str(HTML_REPORT) if HTML_REPORT.is_file() else None,
        "artifacts_directory": str(ARTIFACTS_DIR) if ARTIFACTS_DIR.is_dir() else None,
        "failed_test_instance_count": len(failures),
        "failures": failures,
    }
    FAILURE_CONTEXT_FILE.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return FAILURE_CONTEXT_FILE


def resolve_project_path(path_value: str) -> Path:
    """Resolve a project path and refuse access outside the project."""
    candidate = Path(path_value)
    if not candidate.is_absolute():
        candidate = PROJECT_ROOT / candidate
    resolved = candidate.resolve()
    try:
        resolved.relative_to(PROJECT_ROOT.resolve())
    except ValueError as exc:
        raise ValueError("Path must be inside the project directory.") from exc
    return resolved


@tool
def read_project_file(path: str) -> str:
    """Read a project file, such as a Playwright test source file. Use a project-relative path."""
    file_path = resolve_project_path(path)
    if not file_path.is_file():
        raise FileNotFoundError(f"File not found: {file_path}")
    return file_path.read_text(encoding="utf-8")


@tool
def edit_test_file(path: str, content: str) -> str:
    """Save a healed copy of an original JS/TS test under healed-tests/.

    Pass the original source path from the failure context. If the model
    mistakenly passes a healed-tests/ destination path, resolve its matching
    original under tests/ or generated-tests/ rather than treating the output
    path as the source. The original is never overwritten.
    """
    supplied_path = resolve_project_path(path)
    allowed_suffixes = {".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs"}
    if supplied_path.suffix.lower() not in allowed_suffixes:
        raise ValueError("Only JavaScript/TypeScript source files can be healed.")
    if "test-results" in supplied_path.parts or "playwright-report" in supplied_path.parts:
        raise ValueError("The healer must not edit Playwright result/report folders.")

    project_root = PROJECT_ROOT.resolve()
    source_candidates = []

    try:
        supplied_relative = supplied_path.relative_to(project_root)
    except ValueError as exc:
        raise ValueError("Path must be inside the project directory.") from exc

    # Normal case: path points directly to the original file.
    if supplied_path.is_file() and supplied_relative.parts[0] != "healed-tests":
        source_candidates.append(supplied_path)
    elif supplied_relative.parts and supplied_relative.parts[0] == "healed-tests":
        # The LLM sometimes confuses the output directory with the source.
        inner = Path(*supplied_relative.parts[1:]) if len(supplied_relative.parts) > 1 else Path()
        source_candidates.extend([
            project_root / inner,
            project_root / "tests" / inner,
            project_root / "generated-tests" / inner,
        ])
    else:
        source_candidates.extend([
            project_root / "tests" / supplied_relative,
            project_root / "generated-tests" / supplied_relative,
        ])

    source_file = None
    for candidate in source_candidates:
        candidate = candidate.resolve()
        try:
            candidate.relative_to(project_root)
        except ValueError:
            continue
        if candidate.is_file() and candidate.suffix.lower() in allowed_suffixes:
            if "test-results" not in candidate.parts and "playwright-report" not in candidate.parts and "healed-tests" not in candidate.parts:
                source_file = candidate
                break

    if source_file is None:
        attempted = "\n".join(str(candidate) for candidate in source_candidates)
        raise FileNotFoundError(
            f"Original test file not found for input '{path}'.\n"
            f"Checked these source paths:\n{attempted}"
        )

    relative_path = source_file.relative_to(project_root)
    healed_file = project_root / "healed-tests" / relative_path
    healed_file.parent.mkdir(parents=True, exist_ok=True)
    healed_file.write_text(content, encoding="utf-8")
    return (
        f"Saved healed copy: {healed_file}\n"
        f"Original test left unchanged: {source_file}"
    )


def unique_test_key(failure: dict) -> tuple:
    return (
        failure.get("file", ""),
        failure.get("title", ""),
        failure.get("project", ""),
        failure.get("retry", 0),
    )


async def main() -> None:
    # Read manually generated reports; never launch Playwright tests here.
    failures = collect_failures()
    context_file = write_failure_context(failures)

    print(f"Failed test instances found: {len(failures)}")
    print(f"Consolidated failure context: {context_file}")
    print(f"Existing JSON report (read-only input): {JSON_REPORT}")
    if HTML_REPORT.is_file():
        print(f"Existing HTML report (read-only input): {HTML_REPORT}")
    if ARTIFACTS_DIR.is_dir():
        print(f"Existing artifacts directory (read-only input): {ARTIFACTS_DIR}")

    if not failures:
        print("No failed, timed-out, or interrupted tests found. Nothing to heal.")
        return

    instructions = load_agent_instructions()
    mcp_client = MultiServerMCPClient({
        "playwright": {
            "transport": "stdio",
            "command": "npx",
            "args": ["playwright", "run-test-mcp-server"],
        }
    })
    try:
        playwright_tools = await asyncio.wait_for(
            mcp_client.get_tools(), timeout=MCP_STARTUP_TIMEOUT_SECONDS
        )
    except asyncio.TimeoutError as exc:
        raise TimeoutError(
            f"Playwright MCP startup exceeded {MCP_STARTUP_TIMEOUT_SECONDS} seconds."
        ) from exc
    tools = [*playwright_tools, read_project_file, edit_test_file]

    llm = ChatOllama(model=MODEL_NAME, temperature=0)
    agent = create_agent(model=llm, tools=tools, system_prompt=instructions)

    unique_failures = []
    seen = set()
    for failure in failures:
        key = unique_test_key(failure)
        if key not in seen:
            seen.add(key)
            unique_failures.append(failure)

    for index, failure in enumerate(unique_failures, start=1):
        single_context = {
            "source_report": str(JSON_REPORT),
            "html_report": str(HTML_REPORT) if HTML_REPORT.is_file() else None,
            "artifacts_directory": str(ARTIFACTS_DIR) if ARTIFACTS_DIR.is_dir() else None,
            "failed_test": failure,
        }
        task = f"""
Heal exactly ONE failed test in this invocation. Do not work on any other failure.

Follow the Playwright healer instructions in the system prompt. Use existing
reports, traces, screenshots, and artifacts as investigation inputs where
available. Do not delete, overwrite, clean, regenerate, or otherwise modify the
existing test-results folder, playwright-report folder, or test-run artifacts.
Do not run the entire suite. If verification would overwrite existing artifacts,
do not run it; explain that safe verification was unavailable.

The failed test's canonical original source path is provided in failed_test.file.
Read that exact original file and pass that same path to edit_test_file(path=..., content=...).
NEVER pass a path beginning with healed-tests/ as the source path. edit_test_file
creates the healed-tests/ destination itself. The original test must remain unchanged.
Do not edit result JSON, HTML reports, screenshots, traces, or unrelated tests.
Resolve the MCP test ID using test_list if the JSON report does not contain it.
Make a minimal fix and do not claim success without verification.

This is failed test {index} of {len(unique_failures)}.

Single-test context:
{json.dumps(single_context, indent=2, ensure_ascii=False)}

Consolidated context file: {context_file}
"""
        print(
            f"\n[{index}/{len(unique_failures)}] Healing: "
            f"{failure.get('title')} [{failure.get('project')}] "
            f"({failure.get('file')})"
        )
        # MCP test tools can unexpectedly clean or rewrite Playwright output
        # folders. Snapshot them before each agent run and restore them afterward.
        backup_root, existed = snapshot_preserved_artifacts()
        try:
            result = await asyncio.wait_for(
                agent.ainvoke({
                    "messages": [{"role": "user", "content": task}]
                }),
                timeout=HEALER_TIMEOUT_SECONDS,
            )
            final_message = result["messages"][-1]
            print("\nAgent result:\n")
            print(getattr(final_message, "content", str(final_message)))
        except asyncio.TimeoutError:
            print(
                f"\nTIMEOUT: Healing exceeded {HEALER_TIMEOUT_SECONDS} seconds. "
                "Skipping this test and continuing."
            )
        except Exception as exc:
            print(f"\nERROR while healing this test: {type(exc).__name__}: {exc}")
            print("Skipping this test and continuing with the remaining failures.")
        finally:
            try:
                restore_preserved_artifacts(backup_root, existed)
                print("Preserved test-results/ and playwright-report/ contents restored.")
            except Exception as restore_exc:
                print(f"CRITICAL: {restore_exc}")
                raise


if __name__ == "__main__":
    asyncio.run(main())
