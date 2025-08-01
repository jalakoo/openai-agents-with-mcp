import asyncio
import logging
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
from typing import Dict, Any, Type, Union

load_dotenv()
logger = logging.getLogger(__name__)

class MCPServerManager:
    def __init__(self, servers_config: Dict[str, Dict[str, Any]]):
        """Initialize MCPServerManager with a dictionary of server configurations."""
        self.servers_config = servers_config
        self.server_instances = {}
        self.servers = {}

    def _get_server_class(self, transport: str) -> Type[Union[MCPServerStdio, MCPServerSse, MCPServerStreamableHttp]]:
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
        common_params = {
            'cache_tools_list': config.get('cache_tools_list', True),
        }

        if 'allowed_tools' in config:
            common_params['tool_filter'] = create_static_tool_filter(
                allowed_tool_names=config['allowed_tools']
            )

        transport = transport.lower()
        remaining_config = {k: v for k, v in config.items() if k not in ['allowed_tools', 'cache_tools_list', 'transport']}

        if transport == 'stdio':
            return MCPServerStdioParams(
                **common_params,
                command=remaining_config.pop('command', None),
                args=remaining_config.pop('args', []),
                env=remaining_config.pop('env', None),
                **remaining_config
            )
        elif transport == 'sse':
            return MCPServerSseParams(
                **common_params,
                url=remaining_config.pop('url', None),
                headers=remaining_config.pop('headers', {}),
                **remaining_config
            )
        elif transport == 'http':
            return MCPServerStreamableHttpParams(
                **common_params,
                url=remaining_config.pop('url', None),
                headers=remaining_config.pop('headers', {}),
                **remaining_config
            )
        else:
            raise ValueError(f"Unsupported transport type: {transport}")

    async def __aenter__(self):
        # Create and enter all server contexts
        for server_name, config in self.servers_config.items():
            transport = config.get('transport', 'stdio')
            server_class = self._get_server_class(transport)
            params = self._create_server_params(transport, config)
            server_instance = server_class(params)
            self.server_instances[server_name] = server_instance

        # Enter contexts sequentially
        for server_name, server_instance in self.server_instances.items():
            self.servers[server_name] = await server_instance.__aenter__()

        return self.servers

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        cleanup_errors = []

        # === 1. Trigger shutdown signals if available ===
        for server in self.server_instances.values():
            shutdown_fn = getattr(server, "shutdown", None)
            if callable(shutdown_fn):
                try:
                    await shutdown_fn()
                except Exception as e:
                    logger.warning(f"Error during shutdown signal for {server}: {e}")

        # === 2. Delay briefly to let background tasks settle ===
        # This prevents the stream from closing while a message is still being sent.
        await asyncio.sleep(0.5)  # Adjust timing as needed (500ms to 1s)

        # === 3. Sequentially exit each server context ===
        for server_name, server in reversed(list(self.server_instances.items())):
            try:
                await server.__aexit__(exc_type, exc_val, exc_tb)
            except Exception as e:
                logger.error(f"Error cleaning up server {server_name}: {e}")
                cleanup_errors.append(f"{server_name}: {e}")

        self.servers.clear()
        self.server_instances.clear()

        if cleanup_errors:
            logger.error(f"Encountered {len(cleanup_errors)} error(s) during cleanup.")