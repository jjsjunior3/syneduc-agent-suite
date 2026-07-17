import httpx
import json

MCP_ENDPOINTS = [
    "http://recursos:8000",
]


async def discover_tools():
    registry = {}
    async with httpx.AsyncClient(timeout=10) as client:
        for url in MCP_ENDPOINTS:
            try:
                response = await client.get(f"{url}/tools")
                tools = response.json()

                if isinstance(tools, str):
                    tools = json.loads(tools)

                for tool in tools:
                    tool_id = tool["name"]
                    tags = tool.get("annotations", {}).get("tags", [])

                    search_text = ". ".join([
                        tool.get("name", ""),
                        tool.get("description", ""),
                        ". ".join(tags),
                    ]).lower()

                    registry[tool_id] = {
                        "type": "tool",
                        "server_url": url,
                        "name": tool.get("name"),
                        "description": tool.get("description", ""),
                        "input_schema": tool.get("inputSchema", {}),
                        "tags": tags,
                        "search_text": search_text,
                    }
            except Exception as e:
                print(f"Erro MCP {url}: {e}")

    return registry