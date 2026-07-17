import os
from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.checkpoint.memory import InMemorySaver

load_dotenv()

_llm = ChatOpenAI(
    model="google/gemini-2.5-flash",
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1",
    temperature=0.4,
)

client = MultiServerMCPClient(
    {
        "recursos": {
            "transport": "http",
            "url": "http://recursos:8000/mcp_gateway",
        }
    }
)

memory = InMemorySaver()
agent = None


async def build_agent():
    tools = await client.get_tools()

    agente = create_agent(
        _llm,
        tools=tools,
        system_prompt=(
            "Você é o assistente de Informações do Produto do SynerEduc — "
            "uma plataforma de gestão escolar.\n\n"
            "Seu papel é tirar dúvidas sobre planos, recursos e diferenciais do "
            "SynerEduc, e qualificar o interesse de escolas visitantes.\n\n"
            "Fluxo sugerido:\n"
            "1. Entenda a necessidade (escola, número de alunos, dor principal)\n"
            "2. Use registrar_lead assim que tiver nome da escola, contato, "
            "email, telefone e número de alunos\n"
            "3. Use qualificar_lead para registrar a dor principal e o segmento\n"
            "4. Apresente os planos disponíveis de forma consultiva, sem pressão\n"
            "5. Se o lead quiser fechar, informe que o especialista de contrato "
            "pode gerar uma proposta\n\n"
            "Regras:\n"
            "- Nunca invente preço ou recurso do produto — sempre consulte os planos\n"
            "- Nunca gere proposta você mesmo — isso é responsabilidade do agente de contrato\n"
            "- Seja consultivo, não insistente\n"
        ),
        checkpointer=memory,
    )
    return agente


async def run_agent(mensagem: str, thread_id: str = "1") -> str:
    global agent
    if not agent:
        agent = await build_agent()

    resultado = await agent.ainvoke(
        {"messages": [HumanMessage(content=mensagem)]},
        {"configurable": {"thread_id": thread_id}},
    )
    return resultado["messages"][-1].content