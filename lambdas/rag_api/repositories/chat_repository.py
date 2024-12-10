import os
import uuid
from datetime import datetime
from http import HTTPStatus
from typing import List, Tuple

import pytz
from constants.common_constants import EntryStatus
from models.chat import Chat, ChatIn
from pynamodb.connection import Connection
from pynamodb.exceptions import (
    PutError,
    PynamoDBConnectionError,
    QueryError,
    TableDoesNotExist,
)
from repositories.repository_utils import RepositoryUtils
from utils.logger import logger


class ChatRepository:
    def __init__(self) -> None:
        self.core_obj = 'Chat'
        self.latest_version = 0
        self.conn = Connection(region=os.getenv('REGION'))

    def store_chat(self, chat_in: ChatIn) -> Tuple[HTTPStatus, Chat, str]:
        """Store a new Chat entry.

        :param chat_in: ChatIn object containing the new Chat data.
        :type chat_in: ChatIn

        :return: Tuple containing the HTTP status, the Chat object, and a message.
        :rtype: Tuple[HTTPStatus, Chat, str]

        """
        data = RepositoryUtils.load_data(pydantic_schema_in=chat_in)

        entry_id = str(uuid.uuid4())
        hash_key = f'{self.core_obj}#{chat_in.userId}'
        range_key = f'v{self.latest_version}#{chat_in.chatTopicId}#{entry_id}'
        current_date = datetime.now(tz=pytz.timezone('Asia/Manila')).isoformat()

        try:
            chat_entry = Chat(
                hashKey=hash_key,
                rangeKey=range_key,
                createDate=current_date,
                updateDate=current_date,
                latestVersion=self.latest_version,
                entryStatus=EntryStatus.ACTIVE.value,
                entryId=entry_id,
                **data,
            )
            chat_entry.save()

        except PutError as e:
            message = f'Failed to save chat entry: {str(e)}'
            logger.error(f'[{self.core_obj} = {entry_id}]: {message}')
            return HTTPStatus.INTERNAL_SERVER_ERROR, None, message

        except TableDoesNotExist as db_error:
            message = f'Error on Table, Please check config to make sure table is created: {str(db_error)}'
            logger.error(f'[{self.core_obj} = {entry_id}]: {message}')
            return HTTPStatus.INTERNAL_SERVER_ERROR, None, message

        except PynamoDBConnectionError as db_error:
            message = f'Connection error occurred, Please check config(region, table name, etc): {str(db_error)}'
            logger.error(f'[{self.core_obj} = {entry_id}]: {message}')
            return HTTPStatus.INTERNAL_SERVER_ERROR, None, message

        else:
            logger.info(f'[{self.core_obj} = {entry_id}]: Save Chat Entry Successful')
            return HTTPStatus.OK, chat_entry, None

    def get_chats_in_topic(self, chat_topic_id: str, user_id: str) -> Tuple[HTTPStatus, List[Chat], str]:
        try:
            hash_key = f'{self.core_obj}#{user_id}'
            range_key = f'v{self.latest_version}#{chat_topic_id}#'
            chats = Chat.query(
                hash_key=hash_key,
                range_key_condition=Chat.rangeKey.startswith(range_key),
            )
            chat_list = list(chats)
            if chat_list:
                return HTTPStatus.OK, chat_list, None

            return HTTPStatus.NOT_FOUND, None, 'Chats not found'

        except QueryError as e:
            message = f'Failed to query chat: {str(e)}'
            logger.error(f'[{self.core_obj}={chat_topic_id}] {message}')
            return HTTPStatus.INTERNAL_SERVER_ERROR, None, message

        except TableDoesNotExist as db_error:
            message = f'Error on Table, Please check config to make sure table is created: {str(db_error)}'
            logger.error(f'[{self.core_obj}={chat_topic_id}] {message}')
            return HTTPStatus.INTERNAL_SERVER_ERROR, None, message

        except PynamoDBConnectionError as db_error:
            message = f'Connection error occurred, Please check config(region, table name, etc): {str(db_error)}'
            logger.error(f'[{self.core_obj}={chat_topic_id}] {message}')
            return HTTPStatus.INTERNAL_SERVER_ERROR, None, message
