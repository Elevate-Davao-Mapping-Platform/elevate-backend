from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.data_classes import (
    AppSyncResolverEvent,
    event_source,
)
from aws_lambda_powertools.utilities.typing import LambdaContext
from rag_api.controllers.chat_controller import ChatController
from rag_api.models.chat import ChatPromptIn

logger = Logger()


@logger.inject_lambda_context
@event_source(data_class=AppSyncResolverEvent)
def handler(event: AppSyncResolverEvent, context: LambdaContext) -> dict:
    _ = context

    body = event.arguments

    chat_controller = ChatController()

    chat_in = ChatPromptIn(**body)
    return chat_controller.process_prompt(chat_in)
