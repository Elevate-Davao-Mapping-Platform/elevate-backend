import os
from http import HTTPStatus
from typing import List, Tuple

from aws_lambda_powertools import Logger
from pynamodb.connection import Connection
from pynamodb.exceptions import PynamoDBConnectionError, QueryError, TableDoesNotExist
from shared_modules.constants.entity_constants import EntityType
from shared_modules.models.dynamodb.suggestions import Suggestions


class SuggestionRepository:
    def __init__(self):
        self.conn = Connection(region=os.getenv('REGION'))
        self.logger = Logger()

    def get_suggestions(
        self, entity_type: EntityType, entity_id: str
    ) -> Tuple[HTTPStatus, List[Suggestions], str]:
        """
        Get suggestions for a given entity.

        Args:
            entity_type (EntityType): The type of entity (e.g., EntityType.STARTUP or EntityType.ENABLER)
            entity_id (str): The ID of the entity

        Returns:
            Tuple[HTTPStatus, List[Suggestions], str]: A tuple containing the HTTP status, a list of suggestions, and a message
        """
        try:
            # Get all suggestions for the given entity
            suggestions = Suggestions.query(
                hash_key=f'{entity_type}#{entity_id}',
                range_key_condition=Suggestions.rangeKey.startswith(f'{entity_type}#SUGGESTION#'),
            )

            return HTTPStatus.OK, suggestions, None

        except QueryError as e:
            error_msg = f'Failed to get suggestions: {str(e)}'
            self.logger.error(error_msg)
            return HTTPStatus.NOT_FOUND, None, error_msg

        except (PynamoDBConnectionError, TableDoesNotExist) as e:
            error_msg = f'Failed to get suggestions: {str(e)}'
            self.logger.error(error_msg)
            return HTTPStatus.INTERNAL_SERVER_ERROR, None, error_msg

        except Exception as e:
            error_msg = f'Failed to get suggestions: {str(e)}'
            self.logger.error(error_msg)
            return HTTPStatus.INTERNAL_SERVER_ERROR, None, error_msg
