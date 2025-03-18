import os
import uuid
from datetime import datetime
from http import HTTPStatus
from typing import Tuple

import pytz
from constants.common_constants import EntryStatus
from models.chat_topic import ChatTopic, ChatTopicIn
from pynamodb.connection import Connection
from pynamodb.exceptions import (
    PutError,
    PynamoDBConnectionError,
    QueryError,
    TableDoesNotExist,
)
from utils.logger import logger


class ChatTopicRepository:
    def __init__(self) -> None:
        self.core_obj_key = 'CHAT_TOPIC'
        self.topic_key = 'TOPIC'
        self.conn = Connection(region=os.getenv('REGION'))

    def store_chat_topic(self, chat_topic_in: ChatTopicIn) -> Tuple[HTTPStatus, ChatTopic, str]:
        """Store a new ChatTopic entry."""
        entry_id = str(uuid.uuid4())
        hash_key = f'{self.core_obj_key}#{chat_topic_in.userId}'
        range_key = f'{self.topic_key}#{entry_id}'
        current_date = datetime.now(tz=pytz.timezone('Asia/Manila')).isoformat()

        try:
            chat_topic_entry = ChatTopic(
                hashKey=hash_key,
                rangeKey=range_key,
                createDate=current_date,
                updateDate=current_date,
                entryStatus=EntryStatus.ACTIVE.value,
                entryId=entry_id,
                title=chat_topic_in.title,
            )
            chat_topic_entry.save()

        except PutError as e:
            message = f'Failed to save chat topic: {str(e)}'
            logger.error(f'[{self.core_obj_key} = {entry_id}]: {message}')
            return HTTPStatus.INTERNAL_SERVER_ERROR, None, message

        except TableDoesNotExist as db_error:
            message = f'Error on Table, Please check config to make sure table is created: {str(db_error)}'
            logger.error(f'[{self.core_obj_key} = {entry_id}]: {message}')
            return HTTPStatus.INTERNAL_SERVER_ERROR, None, message

        except PynamoDBConnectionError as db_error:
            message = f'Connection error occurred, Please check config(region, table name, etc): {str(db_error)}'
            logger.error(f'[{self.core_obj_key} = {entry_id}]: {message}')
            return HTTPStatus.INTERNAL_SERVER_ERROR, None, message

        else:
            logger.info(f'[{self.core_obj_key} = {entry_id}]: Save ChatTopic Entry Successful')
            return HTTPStatus.OK, chat_topic_entry, None

    def query_chat_topic(
        self, user_id: str, chat_topic_id: str
    ) -> Tuple[HTTPStatus, ChatTopic, str]:
        try:
            hash_key = f'{self.core_obj_key}#{user_id}'
            range_key = f'{self.topic_key}#{chat_topic_id}'
            range_key_condition = ChatTopic.rangeKey == range_key

            chat_topic_entry = ChatTopic.query(
                hash_key=hash_key,
                range_key_condition=range_key_condition,
            )
            chat_result = list(chat_topic_entry)
            if chat_result or len(chat_result) > 0:
                return HTTPStatus.OK, chat_result[0], None

            return HTTPStatus.NOT_FOUND, None, 'Chat topic not found'

        except QueryError as e:
            message = f'Failed to query chat topic: {str(e)}'
            logger.error(f'[{self.core_obj_key}={chat_topic_id}] {message}')
            return HTTPStatus.INTERNAL_SERVER_ERROR, None, message

        except TableDoesNotExist as db_error:
            message = f'Error on Table, Please check config to make sure table is created: {str(db_error)}'
            logger.error(f'[{self.core_obj_key}={chat_topic_id}] {message}')
            return HTTPStatus.INTERNAL_SERVER_ERROR, None, message

        except PynamoDBConnectionError as db_error:
            message = f'Connection error occurred, Please check config(region, table name, etc): {str(db_error)}'
            logger.error(f'[{self.core_obj_key}={chat_topic_id}] {message}')
            return HTTPStatus.INTERNAL_SERVER_ERROR, None, message
