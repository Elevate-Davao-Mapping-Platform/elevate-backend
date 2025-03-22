from aws_lambda_powertools import Logger
from rag_api.controllers.chat_controller import ChatController
from rag_api.models.chat import ChatPromptIn

logger = Logger()


@logger.inject_lambda_context
def handler(event, context):
    _ = context

    body = event['arguments']

    chat_controller = ChatController()

    chat_in = ChatPromptIn(**body)
    response = chat_controller.process_prompt(chat_in)

    return response
