import os
from http import HTTPStatus
from typing import List, Tuple

from aws_lambda_powertools import Logger
from pynamodb.connection import Connection
from pynamodb.exceptions import PynamoDBConnectionError, QueryError, TableDoesNotExist
from shared_modules.constants.entity_constants import EntityType
from shared_modules.models.dynamodb.entity import Entity


class ProfilesRepository:
    def __init__(self):
        self.conn = Connection(region=os.getenv('REGION'))
        self.logger = Logger()
        self.range_key_discriminator = 'SAVED_PROFILE'

    def get_saved_profiles(
        self, entity_type: EntityType, entity_id: str
    ) -> Tuple[HTTPStatus, List[Entity], str]:
        """
        Get profiles for a given entity.

        Args:
            entity_type (EntityType): The type of entity (e.g., EntityType.STARTUP or EntityType.ENABLER)
            entity_id (str): The ID of the entity

        Returns:
            Tuple[HTTPStatus, List[Profiles], str]: A tuple containing the HTTP status, a list of profiles, and a message
        """
        try:
            hash_key = f'{entity_type}#{entity_id}'
            range_key_prefix = f'{entity_type}#{self.range_key_discriminator}#'
            profiles = Entity.query(
                hash_key=hash_key,
                range_key_condition=Entity.rangeKey.startswith(range_key_prefix),
            )
            profiles_list = list(profiles)
            return HTTPStatus.OK, profiles_list, None

        except QueryError as e:
            error_msg = f'Failed to get profiles: {str(e)}'
            self.logger.error(error_msg)
            return HTTPStatus.NOT_FOUND, None, error_msg

        except (PynamoDBConnectionError, TableDoesNotExist) as e:
            error_msg = f'Failed to get profiles: {str(e)}'
            self.logger.error(error_msg)
            return HTTPStatus.INTERNAL_SERVER_ERROR, None, error_msg

        except Exception as e:
            error_msg = f'Internal server error: {str(e)}'
            self.logger.error(error_msg)
            return HTTPStatus.INTERNAL_SERVER_ERROR, None, error_msg
