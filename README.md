# OpenAI Agents w/ MCP

Example app for using OpenAI Agents with MCP Server(s).


## Requirements
- [uv](https://docs.astral.sh/uv/)
- [OpenAI API Key](https://platform.openai.com)
- [Neo4j Database](https://neo4j.com)
- [Github Personal Access Token](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens)

## Installation
1. Download or clone this repo
2. Run
```
uv sync
```

## Running Simple Example
Runs an interactive CLI agent with a single MCP Stdio server
```
uv run python main_simple.py 
```

## Running Custom Multi Server Example
Runs an interactive CLI agent with multiple mixed MCP servers with a custom MCP Manager
```
uv run python main_multi.py
```

## License
MIT License