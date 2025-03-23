import logging
import os
import sys

from aws_lambda_powertools import Logger
from rag_api.models.chat import ChatPromptIn
from rag_api.usecases.chat_usecase import ChatUsecase


class ChatController:
    def __init__(self):
        self.chat_usecase = ChatUsecase()
        self.logger = Logger()

        is_local = os.getenv('IS_LOCAL')
        if is_local:
            logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
            logging.getLogger().addHandler(logging.StreamHandler(stream=sys.stdout))

    def process_prompt(self, chat_in: ChatPromptIn):
        """
        Process a user prompt and generate a response using a language model.

        :param ChatPromptIn chat_in: The user prompt to generate a response for.
        :return dict: A dictionary containing the response and the status code.
        """
        return self.chat_usecase.process_chat(chat_in)
