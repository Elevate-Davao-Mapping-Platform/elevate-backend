from http import HTTPStatus
from typing import Union

from aws_lambda_powertools import Logger
from rag_api.constants.chat_constants import ChatType
from rag_api.models.chat import ChatIn, ChatOut, ChatPromptIn
from rag_api.models.chat_topic import ChatTopicIn
from rag_api.repositories.chat_repository import ChatRepository
from rag_api.repositories.chat_topic_repository import ChatTopicRepository
from rag_api.usecases.llm_usecase import LLMUsecase
from shared_modules.models.schema.message import ErrorResponse


class ChatUsecase:
    def __init__(self):
        self.chat_repository = ChatRepository()
        self.chat_topic_repository = ChatTopicRepository()
        self.llm_usecase = LLMUsecase()
        self.logger = Logger()

    def process_chat(self, chat_prompt_in: ChatPromptIn) -> Union[ChatOut, ErrorResponse]:
        """
        Process a user prompt and generate a response using a language model.

        :param ChatPromptIn chat_prompt_in: The user prompt to generate a response for.
        :return dict: A dictionary containing the response and the status code.
        """
        status = HTTPStatus.OK
        chat_history = []

        # Create Chat Topic
        chat_topic_id = chat_prompt_in.chatTopicId
        query_chat_topic_status = HTTPStatus.OK
        chat_topic_entry = None

        if chat_topic_id:
            (
                query_chat_topic_status,
                chat_topic_entry,
                _,
            ) = self.chat_topic_repository.query_chat_topic(chat_prompt_in.userId, chat_topic_id)

        if not chat_topic_id or query_chat_topic_status != HTTPStatus.OK:
            status, chat_topic, message = self.chat_topic_repository.store_chat_topic(
                chat_topic_in=ChatTopicIn(
                    userId=chat_prompt_in.userId,
                    title=chat_prompt_in.query,
                    entryId=chat_topic_id,
                )
            )
            if status != HTTPStatus.OK:
                return ErrorResponse(
                    response=message,
                    status=status,
                )

            chat_topic_id = chat_topic.entryId
            chat_prompt_in.chatTopicId = chat_topic_id

        else:
            _, chats, _ = self.chat_repository.get_chats_in_topic(
                chat_topic_id, chat_prompt_in.userId
            )
            chats_sorted = sorted(chats, key=lambda x: x.createdAt, reverse=True)
            chat_history = [chat.message for chat in chats_sorted]

            status, chat_topic_entry, message = self.chat_topic_repository.update_chat_topic(
                chat_topic=chat_topic_entry,
            )
            if status != HTTPStatus.OK:
                return ErrorResponse(
                    response=message,
                    status=status,
                )

        # Store the prompt chat
        user_prompt_chat_in = ChatIn(
            userId=chat_prompt_in.userId,
            chatTopicId=chat_topic_id,
            message=chat_prompt_in.query,
            type=ChatType.USER_PROMPT.value,
            entryId=chat_prompt_in.entryId,
        )
        status, user_prompt_chat, message = self.chat_repository.store_chat(
            chat_in=user_prompt_chat_in,
        )
        if status != HTTPStatus.OK:
            return ErrorResponse(
                response=message,
                status=status,
            )

        chat_history_for_prompt = '\n'.join(chat_history) if chat_history else 'No Chat History'
        llm_response = self.llm_usecase.generate_response(chat_prompt_in, chat_history_for_prompt)

        # Store the response chat
        llm_response_chat_in = ChatIn(
            userId=chat_prompt_in.userId,
            chatTopicId=chat_topic_id,
            message=llm_response,
            type=ChatType.LLM_RESPONSE.value,
        )
        status, _, message = self.chat_repository.store_chat(
            chat_in=llm_response_chat_in,
        )
        if status != HTTPStatus.OK:
            return ErrorResponse(
                response=message,
                status=status,
            )

        return ChatOut(
            response=llm_response,
            chatTopicId=chat_topic_id,
            userId=chat_prompt_in.userId,
            entryId=user_prompt_chat.entryId,
        )
