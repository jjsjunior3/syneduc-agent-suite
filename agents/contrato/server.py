import logging

from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCapabilities, AgentCard, AgentSkill

from executor import ContratoExecutor

logging.basicConfig(level=logging.INFO)

skill = AgentSkill(
    id="contrato",
    name="Contrato e Matrícula SynerEduc",
    description="Conduz o fechamento comercial e gera propostas simuladas de contratação.",
    tags=[
        "contrato",
        "matricula",
        "fechamento",
        "proposta",
        "assinatura",
    ],
    examples=[
        "quero contratar o SynerEduc",
        "quero fechar no plano completo",
        "qual seria o valor para minha escola?",
        "como faço para assinar?",
    ],
)

agent_card = AgentCard(
    name="Agente de Contrato e Matrícula SynerEduc",
    description="Especialista em fechamento comercial e geração de propostas.",
    url="http://contrato_agent:8000/",
    default_input_modes=["text"],
    default_output_modes=["text"],
    skills=[skill],
    version="1.0.0",
    capabilities=AgentCapabilities(),
)

handler = DefaultRequestHandler(
    agent_executor=ContratoExecutor(),
    task_store=InMemoryTaskStore(),
)

server = A2AStarletteApplication(http_handler=handler, agent_card=agent_card)

app = server.build()