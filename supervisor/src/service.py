
import logging
import uuid

import httpx
from a2a.client import A2ACardResolver, ClientFactory, ClientConfig
from a2a.types import Message, Part, Role, TextPart

logger = logging.getLogger(__name__)

HTTPX_CLIENT = httpx.AsyncClient(timeout=30)

BFA_URL = "http://bfa:8000"

# Agente de entrada padrão: quando o BFA não encontra nada com confiança
# e a sessão ainda não tem histórico, cai aqui — é a "porta da frente"
# natural de um funil comercial.
DEFAULT_AGENT_URL = "http://info_produto_agent:8000"

CLIENT_CACHE = {}
SESSION_LAST_AGENT_URL: dict[str, str] = {}


async def resolve_via_bfa(query: str) -> dict | None:
    try:
        response = await HTTPX_CLIENT.get(f"{BFA_URL}/resolve", params={"query": query})
        if response.status_code == 200:
            return response.json()
    except Exception:
        logger.exception("BFA indisponível, usando fallback de sessão")
    return None


async def request_agent(message: str, agent_url: str) -> str:
    if agent_url not in CLIENT_CACHE:
        logger.info(f"Descobrindo AgentCard em {agent_url}")
        resolver = A2ACardResolver(httpx_client=HTTPX_CLIENT, base_url=agent_url)
        agent_card = await resolver.get_agent_card()
        logger.info(f"Agent encontrado: {agent_card.name}")

        config = ClientConfig(httpx_client=HTTPX_CLIENT, streaming=False)
        factory = ClientFactory(config)
        CLIENT_CACHE[agent_url] = factory.create(agent_card)

    client = CLIENT_CACHE[agent_url]

    msg = Message(
        role=Role.user,
        message_id=str(uuid.uuid4()),
        parts=[Part(root=TextPart(text=message))],
    )

    async for event in client.send_message(msg):
        if isinstance(event, Message):
            for part in event.parts:
                if part.root.kind == "text":
                    return part.root.text

    return "Sem resposta do agente."


async def executar_supervisor(texto_usuario: str, session_id: str = "default") -> str:
    resolvido = await resolve_via_bfa(texto_usuario)

    agent_url = None

    if resolvido and resolvido.get("type") not in (None, "no_match", "no_confident_match"):
        best = resolvido["best"]
        tipo = best["type"]

        if tipo == "agent":
            agent_url = best["data"]["agent_url"]
        elif tipo == "tool":
            agent_url = SESSION_LAST_AGENT_URL.get(session_id, DEFAULT_AGENT_URL)

    if not agent_url:
        agent_url = SESSION_LAST_AGENT_URL.get(session_id, DEFAULT_AGENT_URL)

    resposta = await request_agent(texto_usuario, agent_url)

    if "[HANDOFF:contrato]" in resposta:
        resposta = resposta.replace("[HANDOFF:contrato]", "").strip()
        novo_agent_url = "http://contrato_agent:8000"
        SESSION_LAST_AGENT_URL[session_id] = novo_agent_url

        # Transição na mesma mensagem: já chama o agente de contrato
        # com a mensagem original do usuário, para não deixar um turno
        # "vazio" esperando a próxima interação.
        resposta_contrato = await request_agent(texto_usuario, novo_agent_url)

        if resposta:
            return f"{resposta}\n\n---\n\n{resposta_contrato}"
        return resposta_contrato

    SESSION_LAST_AGENT_URL[session_id] = agent_url
    return resposta