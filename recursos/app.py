import os
import random
import json
from typing import Optional, Dict, Any

from fastmcp import FastMCP, Context
from fastmcp.prompts import Message
from starlette.requests import Request
from starlette.responses import JSONResponse

mcp = FastMCP("SynerEduc")
DB_FILE = "/app/db.json"


def load_db() -> Dict[str, Any]:
    if not os.path.exists(DB_FILE):
        return {"planos": {}, "leads": {}, "propostas": {}}
    try:
        with open(DB_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {"planos": {}, "leads": {}, "propostas": {}}


def save_db():
    try:
        with open(DB_FILE, "w") as f:
            json.dump({"planos": planos, "leads": leads, "propostas": propostas}, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print("Erro ao salvar DB:", e)


db = load_db()
planos = db.get("planos", {})
leads = db.get("leads", {})
propostas = db.get("propostas", {})


def extract_resource_data(resource_result) -> Optional[Any]:
    if not resource_result:
        return None
    try:
        if not resource_result.contents:
            return None
        raw = resource_result.contents[0].content
        if isinstance(raw, str):
            return json.loads(raw)
        return raw
    except Exception as e:
        print("Erro extract_resource_data:", e)
        return None


# ===================== RESOURCES (leitura pura) =====================

@mcp.resource("planos://todos")
async def listar_planos():
    return json.dumps(planos, ensure_ascii=False)


@mcp.resource("plano://{plano_id}")
async def obter_plano(plano_id: str):
    data = planos.get(plano_id, {"erro": "Plano não encontrado"})
    return json.dumps(data, ensure_ascii=False)


@mcp.resource("lead://{lead_id}")
async def obter_lead(lead_id: str):
    data = leads.get(lead_id, {"erro": "Lead não encontrado"})
    return json.dumps(data, ensure_ascii=False)


# ===================== PROMPTS =====================

@mcp.prompt
def qualificacao_prompt(nome_escola: str):
    return [
        Message(f"Gestor da escola {nome_escola} demonstrou interesse no SynerEduc."),
        Message("Pergunte a dor principal (ex: gestão de notas manual, comunicação com pais, falta de relatórios) e o número aproximado de alunos.", role="assistant"),
    ]


@mcp.prompt
def proposta_prompt(lead_id: str, plano_id: str):
    return [
        Message(f"Gerar proposta para lead {lead_id} no plano {plano_id}."),
        Message("Apresente valor total estimado (número de alunos x preço por aluno) e deixe claro que é uma simulação, não um contrato formal.", role="assistant"),
    ]


# ===================== TOOLS (ações/mutações) =====================

@mcp.tool(
    name="registrar_lead",
    description="Registra um novo lead (escola interessada) no funil de vendas do SynerEduc.",
    tags={"lead", "cadastro", "vendas"},
    meta={"examples": ["quero saber mais sobre o SynerEduc", "gostaria de contratar para minha escola"]},
)
async def registrar_lead(nome_escola: str, contato: str, email: str, telefone: str, numero_alunos: int, ctx: Context):
    lead_id = str(random.randint(10000, 99999))
    lead = {
        "nome_escola": nome_escola,
        "contato": contato,
        "email": email,
        "telefone": telefone,
        "numero_alunos": numero_alunos,
        "status": "registrado",
    }
    leads[lead_id] = lead
    save_db()
    return {"status": "criado", "lead_id": lead_id, "lead": lead}


@mcp.tool(
    name="qualificar_lead",
    description="Registra a dor principal e o segmento do lead, avançando o funil de qualificação.",
    tags={"lead", "qualificacao", "vendas"},
    meta={"examples": ["a maior dificuldade é o controle de notas manual", "hoje usamos planilha para tudo"]},
)
async def qualificar_lead(lead_id: str, dor_principal: str, segmento: str, ctx: Context):
    resource = await ctx.read_resource(f"lead://{lead_id}")
    data = extract_resource_data(resource)
    if not data or "erro" in data:
        return {"status": "erro", "mensagem": "Lead não encontrado. Registre o lead primeiro."}

    leads[lead_id]["dor_principal"] = dor_principal
    leads[lead_id]["segmento"] = segmento
    leads[lead_id]["status"] = "qualificado"
    save_db()
    return {"status": "qualificado", "lead": leads[lead_id]}


@mcp.tool(
    name="gerar_proposta",
    description="Gera uma proposta comercial simulada (mock) com base no plano escolhido e no número de alunos do lead.",
    tags={"proposta", "contrato", "fechamento"},
    meta={"examples": ["quero fechar no plano completo", "qual seria o valor para 300 alunos?"]},
)
async def gerar_proposta(lead_id: str, plano_id: str, ctx: Context):
    lead_resource = await ctx.read_resource(f"lead://{lead_id}")
    lead = extract_resource_data(lead_resource)
    if not lead or "erro" in lead:
        return {"status": "erro", "mensagem": "Lead não encontrado. Registre e qualifique o lead primeiro."}

    plano_resource = await ctx.read_resource(f"plano://{plano_id}")
    plano = extract_resource_data(plano_resource)
    if not plano or "erro" in plano:
        return {"status": "erro", "mensagem": "Plano não encontrado."}

    valor_total = round(lead["numero_alunos"] * plano["preco_aluno"], 2)
    proposta_id = str(random.randint(100000, 999999))
    proposta = {
        "lead_id": lead_id,
        "plano": plano["nome"],
        "numero_alunos": lead["numero_alunos"],
        "valor_mensal_estimado": valor_total,
        "observacao": "Simulação comercial — não é um contrato formal.",
    }
    propostas[proposta_id] = proposta
    leads[lead_id]["status"] = "proposta_gerada"
    save_db()
    return {"status": "gerada", "proposta_id": proposta_id, "proposta": proposta}


# ===================== Rota REST para o BFA descobrir tools =====================

@mcp.custom_route("/tools", methods=["GET"])
async def list_tools_route(request: Request) -> JSONResponse:
    tools = await mcp.list_tools()
    data = []
    for t in tools:
        data.append({
            "name": t.name,
            "description": t.description or "",
            "inputSchema": t.parameters,
            "annotations": {
                "tags": list(t.tags) if t.tags else [],
                "examples": (t.meta or {}).get("examples", []),
            },
        })
    return JSONResponse(data)