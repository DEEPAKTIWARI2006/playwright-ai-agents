import asyncio
import json
from pathlib import Path
from langchain_ollama import OllamaLLM
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def main():
    llm = OllamaLLM(model="gemma4:31b-cloud")
    config_path = Path("playwright_mcp_config.json")

    with open(config_path, "r", encoding="utf-8") as file:
        config = json.load(file)

    server_params = StdioServerParameters(
        command=config["command"],
        args=config["args"],
    )

    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()

            result = await session.list_tools()

            print("Connected to Playwright MCP server.")
            print("\nAvailable tools:")

            for tool in result.tools:
                print(f"- {tool.name}: {tool.description}")

            # Navigate to a demo website
            response = await session.call_tool(
                "browser_navigate", arguments={"url": "https://playwright.dev"}
            )

            print("\nNavigation result:")
            print(response)

            # Inspect the current webpage
            snapshot = await session.call_tool("browser_snapshot", arguments={})

            print("\nPage snapshot:")
            print(snapshot)

            # Extract text from the MCP snapshot response
            snapshot_text = "\n".join(
                item.text for item in snapshot.content if hasattr(item, "text")
            )

            prompt = f"""
            You are a software test planner.

            Analyze this webpage snapshot and identify:
            1. The purpose of the page.
            2. The visible interactive elements.
            3. Potential test scenarios.
            4. Any information that is missing and needs further exploration.

            Do not assume functionality that is not visible in the snapshot.

            Webpage snapshot:
            {snapshot_text}
            """

            analysis = llm.invoke(prompt)

            print("\nGemma's page analysis:")
            print(analysis)

            # Create the artifacts folder if it doesn't exist
            output_folder = Path("artifacts")
            output_folder.mkdir(exist_ok=True)

            # Save Gemma's analysis
            output_file = output_folder / "page_analysis.md"
            output_file.write_text(analysis, encoding="utf-8")

            print(f"\nAnalysis saved to: {output_file.resolve()}")


if __name__ == "__main__":
    asyncio.run(main())
