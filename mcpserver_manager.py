from agents.mcp import (
    MCPServerStdio,
    MCPServerStdioParams,
    MCPServerSse,
    MCPServerSseParams,
    MCPServerStreamableHttp,
    MCPServerStreamableHttpParams,
    create_static_tool_filter
)
from dotenv import load_dotenv
from typing import Dict, Any, List, Type, Union

load_dotenv()

class MCPServerManager:
    def __init__(self, servers_config: Dict[str, Dict[str, Any]]):
        """Initialize MCPServerManager with a dictionary of server configurations.
        
        Args:
            servers_config: Dictionary where keys are server names and values are 
                          server configuration dictionaries.
        """
        self.servers = {}
        self.server_instances = {}
        self.servers_config = servers_config

    def _get_server_class(self, transport: str) -> Type[Union[MCPServerStdio, MCPServerSse, MCPServerStreamableHttp]]:
        """Get the appropriate server class based on transport type."""
        transport = transport.lower()
        if transport == 'http':
            return MCPServerStreamableHttp
        elif transport == 'sse':
            return MCPServerSse
        elif transport == 'stdio':
            return MCPServerStdio
        else:
            raise ValueError(f"Unsupported transport type: {transport}")

    def _create_server_params(self, transport: str, config: Dict[str, Any]) -> Union[MCPServerStdioParams, MCPServerSseParams, MCPServerStreamableHttpParams]:
        """Create the appropriate parameters object based on transport type."""
        common_params = {
            'cache_tools_list': config.get('cache_tools_list', True),
        }
        
        if 'allowed_tools' in config:
            common_params['tool_filter'] = create_static_tool_filter(
                allowed_tool_names=config['allowed_tools']
            )
        
        transport = transport.lower()
        if transport == 'stdio':
            return MCPServerStdioParams(
                **common_params,
                command=config.get('command'),
                args=config.get('args', []),
                env=config.get('env'),
                **{k: v for k, v in config.items() 
                   if k not in ['command', 'args', 'env', 'allowed_tools', 'cache_tools_list', 'transport']}
            )
        elif transport == 'sse':
            return MCPServerSseParams(
                **common_params,
                url=config.get('url'),
                headers=config.get('headers', {}),
                **{k: v for k, v in config.items() 
                   if k not in ['url', 'headers', 'allowed_tools', 'cache_tools_list', 'transport']}
            )
        elif transport == 'http':
            return MCPServerStreamableHttpParams(
                **common_params,
                url=config.get('url'),
                headers=config.get('headers', {}),
                **{k: v for k, v in config.items() 
                   if k not in ['url', 'headers', 'allowed_tools', 'cache_tools_list', 'transport']}
            )
        else:
            raise ValueError(f"Unsupported transport type: {transport}")

    async def __aenter__(self):
        self.server_instances = {}
        self.servers = {}
        
        # First, create all server instances
        for server_name, config in self.servers_config.items():
            transport = config.get('transport', 'stdio')
            server_class = self._get_server_class(transport)
            
            # Create appropriate parameters object
            params = self._create_server_params(transport, config)
            
            # Create server instance with the parameters
            server = server_class(params)
            
            # Store the server instance for later cleanup
            self.server_instances[server_name] = server
            
        # Then, enter the context for each server
        for server_name, server in self.server_instances.items():
            self.servers[server_name] = await server.__aenter__()
            
        return self.servers

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        # Clean up all servers in reverse order of creation
        cleanup_errors = []
        
        for server_name, server in reversed(list(self.server_instances.items())):
            try:
                # Exit the context manager for this server
                await server.__aexit__(exc_type, exc_val, exc_tb)
            except Exception as e:
                error_msg = f"Error cleaning up server {server_name}: {str(e)}"
                print(error_msg)
                cleanup_errors.append(error_msg)
        
        # Clear references
        self.servers.clear()
        self.server_instances.clear()
        
        if cleanup_errors:
            print(f"\nEncountered {len(cleanup_errors)} error(s) during cleanup:")
            for error in cleanup_errors:
                print(f"- {error}")