import logging

from a2a.server.agent_execution import AgentExecutor
from a2a.server.agent_execution.context import RequestContext
from a2a.server.events.event_queue import EventQueue
from a2a.utils import new_agent_text_message

from agent.info_produto import run_agent

logger = logging.getLogger("a2a")


class InfoProdutoExecutor(AgentExecutor):
    async def execute(self, context: RequestContext, event_queue: EventQueue):
        logger.info("agent.execute.info_produto")

        user_text = context.get_user_input()
        resposta = await run_agent(mensagem=user_text)

        await event_queue.enqueue_event(new_agent_text_message(str(resposta)))

    async def cancel(self, context: RequestContext, event_queue: EventQueue):
        logger.info("agent.cancel.info_produto")