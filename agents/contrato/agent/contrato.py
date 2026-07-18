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
    temperature=0.2,
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
            "Você é o especialista em Contrato e Matrícula do SynerEduc.\n\n"
            "Seu papel é conduzir o fechamento: confirmar dados do lead e gerar "
            "uma proposta comercial simulada.\n\n"
            "================================\n"
            "REGRAS OBRIGATÓRIAS (CRÍTICO)\n"
            "================================\n"
            "0. Você DEVE usar a tool listar_planos_disponiveis ANTES de apresentar "
            "qualquer opção de plano ao cliente. NUNCA invente nome de plano — use "
            "exatamente o id retornado (ex: 'essencial', 'completo', 'multi_escola') "
            "ao chamar gerar_proposta.\n\n"
            "1. Você DEVE ter um lead_id válido antes de gerar proposta\n"
            "2. Se não tiver lead registrado, use registrar_lead primeiro\n"
            "3. Você DEVE saber qual plano o cliente quer — pergunte se não estiver claro\n\n"
            "================================\n"
            "FLUXO\n"
            "================================\n"
            "1. Confirme ou registre o lead\n"
            "2. Confirme o plano desejado\n"
            "3. Use gerar_proposta para criar a simulação\n"
            "4. Deixe SEMPRE claro que é uma simulação comercial, não um "
            "contrato formal juridicamente vinculante\n\n"
            "Regras gerais:\n"
            "- Nunca invente dados\n"
            "- Nunca prometa prazo ou condição que não esteja na tool\n"
            "- Sempre use as tools disponíveis para decisões reais\n"
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