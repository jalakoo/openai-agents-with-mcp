from agents import Agent, Runner
from agents.mcp import MCPServerStdio
from dotenv import load_dotenv
import asyncio
import os

load_dotenv()


async def interactive_main():

    async with MCPServerStdio(
        cache_tools_list=True,  # Cache the tools list to reduce reuse latency
        params={
            "command": "uvx",
            "args": ["mcp-neo4j-cypher@0.3.0", "--transport", "stdio"],
            "env": os.environ,
        },
    ) as server:

        # Create an agent to use the tool(s) from the MCP Server
        agent = Agent(
            name="OpenAI + MCP Agent",
            instructions=f"Read or write data to a Neo4j database based on user instructions",
            mcp_servers=[server],
            model=os.environ.get("OPENAI_MODEL"),
        )

        # Execute the user request to the agent
        # Instructions
        print("\nType your request (or 'exit' to quit):")

        # Start loop
        while True:

            user_input = input("👶 You: ").strip()

            # Exit condition
            if user_input.lower() in {"exit", "quit"}:
                print("Exiting interactive session.")
                break

            try:

                result = await Runner.run(starting_agent=agent, input=user_input)

                # Print just the answer part to the interactive session
                print(f"\n🤖 Agent: {result.final_output}\n")
            except Exception as e:
                print(f"\nError processing request: {str(e)}\n")


if __name__ == "__main__":
    asyncio.run(interactive_main())
