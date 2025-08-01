from agents import Agent, Runner, SQLiteSession
from mcpserver_manager import MCPServerManager
from dotenv import load_dotenv
import asyncio
import os

load_dotenv()

# Simple retry function for agent runs
async def run_with_retry(agent, user_input, session, max_retries=2):
    for attempt in range(1, max_retries + 1):
        try:
            return await Runner.run(starting_agent=agent, input=user_input, session=session)
        except Exception as e:
            if attempt == max_retries:
                print(f"\n❌ Error: {str(e)}")
                return None
            print(f"\n⚠️  Retrying... (attempt {attempt}/{max_retries})")
            await asyncio.sleep(1)  # Simple 1-second delay between retries
    return None

async def main():

    # Custom MCP Server Configs with explicit tool filtering
    # Mostly matches standard MCP server config options
    # Added `allowed_tools` and `cache_tools_list` specific to OpenAI Agents implementation
    servers_config = {
        'neo4j-database': {
            'command': 'uvx',
            'args': ['mcp-neo4j-cypher@0.3.0', '--transport', 'stdio'],
            'env': os.environ,
            'transport': 'stdio',
            'allowed_tools': [
                'read_neo4j_cypher', 
                'write_neo4j_cypher', 
                'get_neo4j_schema'
            ],
            'cache_tools_list': True
        },
        # Github MCP server configuration
        'github': {
            'url': 'https://api.githubcopilot.com/mcp',
            'headers': {
                'Authorization': f'Bearer {os.environ.get("GITHUB_TOKEN")}'
            },
            'allowed_tools': [
                'search_repositories', 
                'search_users', 
                'get_me'
            ],
            'transport': 'http',
            'cache_tools_list': True
        },
        # Add more server configs as needed
    }
    
    async with MCPServerManager(servers_config) as server_instances:
        
        # Print the names of the servers that were started
        print(f'Servers started: {list(server_instances.keys())}')

        # Create an agent with optimized configuration
        agent = Agent(
            name="Neo4j MCP + Github Agent",
            instructions=(
                "You are a helpful assistant that works with GitHub and Neo4j. "
                "When asked to work with repositories, first check what's available in the database "
                "before making external API calls. Keep responses concise and focused on the task."
            ),
            mcp_servers=list(server_instances.values()),
            model=os.environ.get("OPENAI_MODEL"), 
        )

        # Create a session to manage memory
        session = SQLiteSession("MCP Conversation history")

        print("\nType your request (or 'exit' to quit):")

        # Start an interactive session
        while True:
            try:
                user_input = input("👶 You: ").strip()
                if user_input.lower() in {"exit", "quit"}:
                    print("Exiting interactive session.")
                    break
                
                # Replace with `await Runner.run(starting_agent=agent, input=user_input, session=session)` to go without simple retry
                result = await run_with_retry(agent, user_input, session)

                if result:
                    print(f"\n🤖 Agent: {result.final_output}\n")
                
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"\n❌ Error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())