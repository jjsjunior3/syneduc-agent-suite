# SynerEduc Agent Suite — AI-Powered Sales & Product Assistant

A multi-agent sales assistant applying modern AI agent protocols — **A2A** (Agent-to-Agent), **MCP** (Model Context Protocol), and **BFA** (Backend For Agents) — to a real business domain: qualifying leads and generating commercial proposals for [SynerEduc](https://github.com/jjsjunior3/SynerEduc), a school management SaaS in production.

> This is a companion project to [md-bank-agents](https://github.com/jjsjunior3/md-bank-agents), where I first implemented these protocols following a structured course. Here, I apply the same architecture independently, from scratch, to a domain I designed myself — a sales funnel for my own product — with an upgraded routing design (BFA as the sole discovery layer, no hardcoded fallback dictionary).

---

## Why this project exists

Most course-based agent projects stay in their original fictional domain. I wanted to prove the pattern generalizes: same protocols, same architectural discipline, applied to a problem I actually have — helping schools discover and evaluate SynerEduc, and simulating the path from "just looking" to "ready to sign."

## Architecture overview

```
                Usuário
                   │
                   ▼
             Frontend (Streamlit)
                   │
                   ▼
              Supervisor
        (session-aware A2A router)
                   │
             GET /resolve
                   ▼
                 BFA
      (dynamic catalog + BM25 ranking)
              /              \
           A2A               A2A
            /                    \
  Agente: Info Produto      Agente: Contrato
   (consultivo, só lê)      (executa ações, fecha)
            \                    /
           MCP                MCP
              \              /
                 Recursos
             (FastMCP server)
        Tools · Resources · Prompts
```

Every box is an independent Docker container. Agents share no memory and import no code from each other — only protocol.

## Protocols in practice

| Protocol | Role | Where it lives |
|---|---|---|
| **A2A** | Agent discovery and communication via Agent Cards over HTTP/JSON-RPC. Neither the Supervisor nor the BFA hardcode agent URLs. | `supervisor/src/service.py`, `bfa/discovery.py`, `agents/*/server.py` |
| **MCP** | Structured tools (`registrar_lead`, `qualificar_lead`, `gerar_proposta`), resources (`plano://{id}`, `lead://{id}`), and prompts, served by a dedicated FastMCP server. Agents never invent plan names or prices — every commercial fact comes from a tool call. | `recursos/app.py`, `agents/*/agent/*.py` |
| **BFA** | The *only* routing path — there is no static agent dictionary in the Supervisor. On startup, the BFA discovers every agent (via A2A) and every tool (via a custom MCP REST route), builds a BM25 search index, and resolves each user message to the best matching agent or tool with a confidence score. | `bfa/` (`discovery.py`, `mcp_discovery.py`, `registry.py`, `app.py`) |

### Design decisions worth noting

- **BFA-first, not BFA-as-fallback**: in the companion MD Bank project, the BFA was an optional alternate route alongside a hardcoded agent dictionary. Here, the Supervisor has *no* hardcoded agent list at all — adding a third agent requires zero changes to the Supervisor's code, only a new endpoint in the BFA's discovery config.
- **Two agents, two responsibilities, enforced by prompt**: the Product Info agent is explicitly forbidden from generating proposals; the Contract agent is explicitly forbidden from inventing plan names or prices. Each agent only has the tools that match its responsibility.
- **Inline handoff signaling**: when the Product Info agent detects clear purchase intent, it appends an internal `[HANDOFF:contrato]` marker to its response. The Supervisor strips the marker, routes the *same* message to the Contract agent, and merges both replies into a single turn — no awkward "please type something else to continue" gap for the user.
- **Session-isolated agent memory**: each domain agent keeps its own `InMemorySaver` checkpointer. When a user is handed off to the Contract agent, that agent has no memory of the prior conversation with the Product Info agent — it asks for the lead ID again. This is a deliberate architectural boundary (mirrors real organizational handoffs), not a bug — documented here so it reads as intentional, because on first glance it looks like a rough edge.
- **Mock data only**: `recursos/db.json` is a self-contained fictional dataset (fake plans, fake leads). This project never connects to SynerEduc's real production database.

## A real debugging story

During testing, the Contract agent kept claiming a "technical problem" listing plans, despite every HTTP call in the logs returning `200 OK`. The root cause wasn't in the code — it was a `db.json` that had been seeded empty on first run and never received its actual plan data before being committed to disk by a `save_db()` call. Found by systematically eliminating layers: zero-argument MCP tool schema (verified fine), stale conversation memory (ruled out), stopped containers (ruled out), MCP protocol-level errors (ruled out via direct Insomnia tool calls) — until the tool's raw JSON response revealed `"planos": {}`. A reminder that clean HTTP logs don't guarantee correct data.

## Tech stack

- **Orchestration**: LangChain (`create_agent`), `InMemorySaver` for per-agent conversation memory
- **Agents**: Google Gemini 2.5 Flash via OpenRouter
- **Protocols**: `a2a-sdk`, `fastmcp`
- **Discovery/Ranking**: `rank-bm25` + `numpy`
- **Backend**: FastAPI (Supervisor, BFA, domain agents), Starlette (A2A servers)
- **Frontend**: Streamlit
- **Infra**: Docker Compose, one container per service

## Project structure

```
syneduc-agent-suite/
├── docker-compose.yml
├── supervisor/          # A2A client + BFA-driven routing + session tracking
├── bfa/                 # Backend For Agents: discovery + BM25 resolution
├── agents/
│   ├── info_produto/    # Product info agent (A2A server, read-only)
│   └── contrato/        # Contract/enrollment agent (A2A server, executes actions)
├── recursos/            # MCP server (tools, resources, prompts, mock DB)
└── frontend/             # Streamlit chat UI
```

## Running locally

Requires Docker Desktop.

```bash
git clone https://github.com/jjsjunior3/syneduc-agent-suite.git
cd syneduc-agent-suite
cp agents/info_produto/.env.example agents/info_produto/.env
cp agents/contrato/.env.example agents/contrato/.env
# fill in OPENROUTER_API_KEY in both .env files

docker compose up --build
```

| Service | URL |
|---|---|
| Chat (Streamlit) | http://localhost:9090 |
| Supervisor API | http://localhost:8080/docs |
| BFA discovery API | http://localhost:8083/docs |
| MCP server (Insomnia/MCP client) | http://localhost:8084/mcp_gateway |

### Trying the BFA directly

```bash
curl "http://localhost:8083/resolve?query=quero saber sobre os planos"
curl "http://localhost:8083/resolve?query=quero fechar contrato"
curl http://localhost:8083/agents
curl http://localhost:8083/tools
```

## What I'd build next

- React front-end with AG-UI streaming (the fourth protocol from the companion MD Bank project — planned, not yet built here)
- Pass `lead_id` automatically from the Product Info agent's session into the Contract agent handoff, instead of asking the user to repeat it
- Persist checkpointer state (Redis) instead of in-memory
- Add automated tests for BFA resolution and handoff logic
- Real proposal PDF generation instead of a JSON mock

## About this project

Built by [José João Santos Júnior](https://github.com/jjsjunior3) — part of a self-directed path into AI agent engineering, applying protocols studied in a structured course to a domain of my own: the sales funnel for [SynerEduc](https://github.com/jjsjunior3/SynerEduc), a school management SaaS I built and operate in production.