import logging

from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCapabilities, AgentCard, AgentSkill

from executor import InfoProdutoExecutor

logging.basicConfig(level=logging.INFO)

skill = AgentSkill(
    id="info_produto",
    name="Informações do Produto SynerEduc",
    description="Tira dúvidas sobre planos, recursos e diferenciais do SynerEduc, e qualifica leads.",
    tags=[
        "synereduc",
        "planos",
        "precos",
        "recursos do produto",
        "gestao escolar",
        "informacoes",
    ],
    examples=[
        "quero saber mais sobre o SynerEduc",
        "quais planos vocês oferecem?",
        "quanto custa para 200 alunos?",
        "o que o SynerEduc resolve?",
    ],
)

agent_card = AgentCard(
    name="Agente de Informações do Produto SynerEduc",
    description="Especialista em apresentar o SynerEduc e qualificar interesse de escolas.",
    url="http://info_produto_agent:8000/",
    default_input_modes=["text"],
    default_output_modes=["text"],
    skills=[skill],
    version="1.0.0",
    capabilities=AgentCapabilities(),
)

handler = DefaultRequestHandler(
    agent_executor=InfoProdutoExecutor(),
    task_store=InMemoryTaskStore(),
)

server = A2AStarletteApplication(http_handler=handler, agent_card=agent_card)

app = server.build()