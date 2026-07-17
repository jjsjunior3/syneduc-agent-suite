import asyncio
import httpx
from a2a.client import A2ACardResolver

AGENT_ENDPOINTS = [
    "http://info_produto_agent:8000",
    "http://contrato_agent:8000",
]


def normalize(text):
    if not text:
        return ""
    return text.lower().strip()


async def discover_agents():
    registry = {}
    async with httpx.AsyncClient(timeout=5) as client:
        for url in AGENT_ENDPOINTS:
            for attempt in range(3):
                try:
                    resolver = A2ACardResolver(httpx_client=client, base_url=url)
                    card = await resolver.get_agent_card()

                    for skill in card.skills:
                        registry[skill.id] = {
                            "agent_url": url,
                            "name": skill.name,
                            "description": skill.description,
                            "tags": skill.tags,
                            "examples": skill.examples,
                            "search_text": ". ".join(
                                filter(None, [skill.name, skill.description, ". ".join(skill.tags or [])])
                            ).lower(),
                            "type": "agent",
                        }
                    break
                except Exception as e:
                    print(f"Tentativa {attempt+1} falhou para {url}: {e}")
                    await asyncio.sleep(2)
    return registry