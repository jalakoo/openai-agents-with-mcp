from agents import Agent, Runner
from agents.mcp import MCPServerStdio, create_static_tool_filter
from dotenv import load_dotenv
import asyncio
import os

load_dotenv()

allowed_tools = ["read_neo4j_cypher", "write_neo4j_cypher", "get_neo4j_schema"]

# async def main(user_input:str):

#     # Simple example following OpenAI's quickstart
#     # Create context manager for MCP stdio server
#     # Replace with MCPServerSse or MCPServerStreamableHttp as needed
#     # Optionally define allowed tools
#     # allowed_tools = ["read_neo4j_cypher", "write_neo4j_cypher", "get_neo4j_schema"]
    
#     # # Create tool filter first
#     # tool_filter = create_static_tool_filter(allowed_tool_names=allowed_tools)
    
#     async with MCPServerStdio(
#         cache_tools_list=True,  # Cache the tools list to reduce reuse latency
#         params={
#             "command": "uvx",
#             "args": ["mcp-neo4j-cypher@0.2.4", "--transport", "stdio"],
#             "env": os.environ
#         },
#         # tool_filter=tool_filter # Remove if not needing to filter tools
#         tool_filter=create_static_tool_filter(allowed_tool_names=allowed_tools)
#     ) as server:   
        
#         all_tools = await server.list_tools()
#         print(f'All tools found: {all_tools}')

#         # Create an agent to use the tool(s) from the MCP Server
#         agent = Agent(
#             name="OpenAI Agent + Neo4j MCP Agent",
#             instructions=f"Read or write data to a Neo4j database based on user instructions",
#             mcp_servers=[server],
#             model=os.environ.get("OPENAI_MODEL"), 
#         )

#         # Execute the user request to the agent
#         return await Runner.run(starting_agent=agent, input=user_input)


async def interactive_main():

    async with MCPServerStdio(
        cache_tools_list=True,  # Cache the tools list to reduce reuse latency
        params={
            "command": "uvx",
            "args": ["mcp-neo4j-cypher@0.3.0", "--transport", "stdio"],
            "env": os.environ
        },
        # tool_filter=tool_filter # Remove if not needing to filter tools
        tool_filter=create_static_tool_filter(allowed_tool_names=allowed_tools)
    ) as server:  


        # all_tools = await server.list_tools()
        # print(f'All tools found: {all_tools}')

        # Create an agent to use the tool(s) from the MCP Server
        agent = Agent(
            name="OpenAI Agent + Neo4j MCP Agent",
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
            if user_input.lower() in {"exit", "quit"}:
                print("Exiting interactive session.")
                break
            try:

                result =  await Runner.run(starting_agent=agent, input=user_input)
                        
                # Print just the answer part in the interactive session
                print(f"\n🤖 Agent: {result.final_output}\n")
            except Exception as e:
                print(f"\nError processing request: {str(e)}\n")

if __name__ == "__main__":
    asyncio.run(interactive_main())