import logging
import os
import sys
from http import HTTPStatus

from aws_lambda_powertools import Logger
from rag_api.constants.chat_constants import ChatType
from rag_api.models.chat import ChatIn, ChatOut, ChatPromptIn
from rag_api.models.chat_topic import ChatTopicIn
from rag_api.repositories.chat_repository import ChatRepository
from rag_api.repositories.chat_topic_repository import ChatTopicRepository
from rag_api.usecases.llm_usecase import LLMUsecase


class ChatController:
    def __init__(self):
        self.chat_repository = ChatRepository()
        self.chat_topic_repository = ChatTopicRepository()
        self.llm_usecase = LLMUsecase()
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
        status = HTTPStatus.OK

        chat_topic_id = chat_in.chatTopicId
        if chat_topic_id:
            status, _, message = self.chat_topic_repository.query_chat_topic(
                chat_in.userId, chat_topic_id
            )

        if not chat_topic_id or status != HTTPStatus.OK:
            status, chat_topic, message = self.chat_topic_repository.store_chat_topic(
                chat_topic_in=ChatTopicIn(
                    userId=chat_in.userId,
                    title=chat_in.query,
                )
            )
            if status != HTTPStatus.OK:
                return {
                    'response': message,
                    'status': status,
                }

            chat_topic_id = chat_topic.entryId

        _, chats, _ = self.chat_repository.get_chats_in_topic(chat_topic_id, chat_in.userId)

        chats = chats or []
        chats = sorted(chats, key=lambda x: x.createDate, reverse=True)
        chat_history_for_prompt = '\n'.join([chat.message for chat in chats])

        llm_response = self.llm_usecase.generate_response(chat_in, chat_history_for_prompt)

        if llm_response['status'] != HTTPStatus.OK:
            return llm_response

        # Store the query chat
        user_prompt_chat_in = ChatIn(
            userId=chat_in.userId,
            chatTopicId=chat_topic_id,
            message=chat_in.query,
            type=ChatType.USER_PROMPT.value,
            entryId=chat_in.entryId,
        )
        status, user_prompt_chat, message = self.chat_repository.store_chat(
            chat_in=user_prompt_chat_in,
        )
        if status != HTTPStatus.OK:
            return {
                'response': message,
                'status': status,
            }

        # Store the response chat
        llm_response_chat_in = ChatIn(
            userId=chat_in.userId,
            chatTopicId=chat_topic_id,
            message=llm_response['response'],
            type=ChatType.LLM_RESPONSE.value,
        )
        status, _, message = self.chat_repository.store_chat(
            chat_in=llm_response_chat_in,
        )
        if status != HTTPStatus.OK:
            return {
                'response': message,
                'status': status,
            }

        chat_data = ChatOut(
            response=llm_response['response'],
            chatTopicId=chat_topic_id,
            userId=chat_in.userId,
            entryId=user_prompt_chat.entryId,
        )
        return chat_data.model_dump()
