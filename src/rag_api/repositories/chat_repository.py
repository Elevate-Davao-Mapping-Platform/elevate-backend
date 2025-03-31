import os
import uuid
from datetime import datetime
from http import HTTPStatus
from typing import List, Tuple

import pytz
from aws_lambda_powertools import Logger
from pynamodb.connection import Connection
from pynamodb.exceptions import (
    PutError,
    PynamoDBConnectionError,
    QueryError,
    TableDoesNotExist,
)
from rag_api.models.chat import Chat, ChatIn
from shared_modules.constants.common_constants import EntryStatus


class ChatRepository:
    def __init__(self) -> None:
        self.core_obj_key = 'CHAT'
        self.topic_key = 'TOPIC'
        self.message_key = 'MESSAGE'
        self.conn = Connection(region=os.getenv('REGION'))
        self.logger = Logger()

    def store_chat(self, chat_in: ChatIn) -> Tuple[HTTPStatus, Chat, str]:
        """Store a new Chat entry.

        :param chat_in: ChatIn object containing the new Chat data.
        :type chat_in: ChatIn

        :return: Tuple containing the HTTP status, the Chat object, and a message.
        :rtype: Tuple[HTTPStatus, Chat, str]

        """
        if not chat_in.entryId:
            chat_in.entryId = str(uuid.uuid4())

        entry_id = chat_in.entryId

        hash_key = f'{self.core_obj_key}#{chat_in.userId}#{self.topic_key}#{chat_in.chatTopicId}'
        range_key = f'{self.message_key}#{entry_id}'
        current_date = datetime.now(tz=pytz.timezone('Asia/Manila')).isoformat()

        data = chat_in.model_dump()

        try:
            chat_entry = Chat(
                hashKey=hash_key,
                rangeKey=range_key,
                createdAt=current_date,
                updateDate=current_date,
                entryStatus=EntryStatus.ACTIVE.value,
                **data,
            )
            chat_entry.save()

        except PutError as e:
            message = f'Failed to save chat entry: {str(e)}'
            self.logger.exception(f'[{self.core_obj_key} = {entry_id}]: {message}')
            return HTTPStatus.INTERNAL_SERVER_ERROR, None, message

        except TableDoesNotExist as db_error:
            message = f'Error on Table, Please check config to make sure table is created: {str(db_error)}'
            self.logger.exception(f'[{self.core_obj_key} = {entry_id}]: {message}')
            return HTTPStatus.INTERNAL_SERVER_ERROR, None, message

        except PynamoDBConnectionError as db_error:
            message = f'Connection error occurred, Please check config(region, table name, etc): {str(db_error)}'
            self.logger.exception(f'[{self.core_obj_key} = {entry_id}]: {message}')
            return HTTPStatus.INTERNAL_SERVER_ERROR, None, message

        else:
            self.logger.info(f'[{self.core_obj_key} = {entry_id}]: Save Chat Entry Successful')
            return HTTPStatus.OK, chat_entry, None

    def get_chats_in_topic(
        self, chat_topic_id: str, user_id: str
    ) -> Tuple[HTTPStatus, List[Chat], str]:
        try:
            hash_key = f'{self.core_obj_key}#{user_id}#{self.topic_key}#{chat_topic_id}'
            chats = Chat.query(hash_key=hash_key)
            chat_list = list(chats)
            if chat_list:
                return HTTPStatus.OK, chat_list, None

            return HTTPStatus.NOT_FOUND, None, 'Chats not found'

        except QueryError as e:
            message = f'Failed to query chat: {str(e)}'
            self.logger.exception(f'[{self.core_obj_key}={chat_topic_id}] {message}')
            return HTTPStatus.INTERNAL_SERVER_ERROR, None, message

        except TableDoesNotExist as db_error:
            message = f'Error on Table, Please check config to make sure table is created: {str(db_error)}'
            self.logger.exception(f'[{self.core_obj_key}={chat_topic_id}] {message}')
            return HTTPStatus.INTERNAL_SERVER_ERROR, None, message

        except PynamoDBConnectionError as db_error:
            message = f'Connection error occurred, Please check config(region, table name, etc): {str(db_error)}'
            self.logger.exception(f'[{self.core_obj_key}={chat_topic_id}] {message}')
            return HTTPStatus.INTERNAL_SERVER_ERROR, None, message
