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
from repositories.repository_utils import RepositoryUtils
from utils.logger import logger


class ChatTopicRepository:
    def __init__(self) -> None:
        self.core_obj = 'ChatTopic'
        self.latest_version = 0
        self.conn = Connection(region=os.getenv('REGION'))

    def store_chat_topic(self, chat_topic_in: ChatTopicIn) -> Tuple[HTTPStatus, ChatTopic, str]:
        """Store a new ChatTopic entry."""
        entry_id = str(uuid.uuid4())
        data = RepositoryUtils.load_data(pydantic_schema_in=chat_topic_in)
        hash_key = f'{self.core_obj}#{chat_topic_in.userId}'
        range_key = f'v{self.latest_version}#{entry_id}'
        current_date = datetime.now(tz=pytz.timezone('Asia/Manila')).isoformat()

        try:
            chat_topic_entry = ChatTopic(
                hashKey=hash_key,
                rangeKey=range_key,
                createDate=current_date,
                updateDate=current_date,
                latestVersion=self.latest_version,
                entryStatus=EntryStatus.ACTIVE.value,
                entryId=entry_id,
                **data,
            )
            chat_topic_entry.save()

        except PutError as e:
            message = f'Failed to save chat topic: {str(e)}'
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
            logger.info(f'[{self.core_obj} = {entry_id}]: Save ChatTopic Entry Successful')
            return HTTPStatus.OK, chat_topic_entry, None

    def query_chat_topic(self, user_id: str, chat_topic_id: str) -> Tuple[HTTPStatus, ChatTopic, str]:
        try:
            hash_key = f'{self.core_obj}#{user_id}'
            range_key = f'v{self.latest_version}#{chat_topic_id}'
            chat_topic_entry = ChatTopic.query(
                ChatTopic.hashKey == hash_key,
                ChatTopic.rangeKey == range_key,
            )
            if chat_topic_entry:
                return HTTPStatus.OK, chat_topic_entry, None

            return HTTPStatus.NOT_FOUND, None, 'Chat topic not found'

        except QueryError as e:
            message = f'Failed to query chat topic: {str(e)}'
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
