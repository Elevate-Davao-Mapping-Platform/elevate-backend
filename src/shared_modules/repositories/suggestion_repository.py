import os
from datetime import datetime
from http import HTTPStatus
from typing import List, Tuple
from uuid import uuid4

import pytz
from aws_lambda_powertools import Logger
from pynamodb.connection import Connection
from pynamodb.exceptions import PynamoDBConnectionError, QueryError, TableDoesNotExist
from shared_modules.constants.entity_constants import EntityType
from shared_modules.models.dynamodb.entity import Entity
from shared_modules.models.dynamodb.suggestions import Suggestions
from shared_modules.models.schema.suggestions import SuggestionMatchList


class SuggestionRepository:
    def __init__(self):
        self.conn = Connection(region=os.getenv('REGION'))
        self.logger = Logger()
        self.suggestion_discriminator = 'SUGGESTION'
        self.saved_profile_discriminator = 'SAVED_PROFILE'

    def get_suggestions(
        self, entity_type: EntityType, entity_id: str
    ) -> Tuple[HTTPStatus, List[Entity], List[Entity], str]:
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
            entities = Entity.query(
                hash_key=f'{entity_type}#{entity_id}',
            )

            saved_profiles = []
            suggestions = []

            for entity in entities:
                if entity.rangeKey.startswith(f'{entity_type}#{self.saved_profile_discriminator}#'):
                    saved_profiles.append(entity)
                elif entity.rangeKey.startswith(f'{entity_type}#{self.suggestion_discriminator}#'):
                    suggestions.append(entity)

            return HTTPStatus.OK, suggestions, saved_profiles, None

        except QueryError as e:
            error_msg = f'Failed to get suggestions: {str(e)}'
            self.logger.error(error_msg)
            return HTTPStatus.NOT_FOUND, None, None, error_msg

        except (PynamoDBConnectionError, TableDoesNotExist) as e:
            error_msg = f'Failed to get suggestions: {str(e)}'
            self.logger.error(error_msg)
            return HTTPStatus.INTERNAL_SERVER_ERROR, None, None, error_msg

        except Exception as e:
            error_msg = f'Internal server error: {str(e)}'
            self.logger.error(error_msg)
            return HTTPStatus.INTERNAL_SERVER_ERROR, None, None, error_msg

    def save_suggestions(self, suggestion_list: SuggestionMatchList) -> Tuple[HTTPStatus, str, str]:
        """
        Save suggestion matches using batch write operation.

        Args:
            suggestion_list (SuggestionMatchList): List of suggestion matches to save
        """
        try:
            with Suggestions.batch_write() as batch:
                for match in suggestion_list.matches:
                    # Create two suggestions (one for each entity in the pair)
                    for i, entity in enumerate(match.matchPair):
                        other_entity = match.matchPair[1 - i]  # Get the other entity in the pair

                        suggestion_id = str(uuid4())
                        current_date = datetime.now(tz=pytz.timezone('Asia/Manila')).isoformat()
                        match_pair_id = f'{other_entity.entityType}#{other_entity.entityId}'

                        suggestion = Suggestions(
                            hashKey=f'{entity.entityType}#{entity.entityId}',
                            rangeKey=f'{entity.entityType}#SUGGESTION#{match_pair_id}',
                            suggestionId=suggestion_id,
                            matchPairId=match_pair_id,
                            matchPairName=other_entity.name,
                            matchPairType=other_entity.entityType,
                            certainty=match.certainty,
                            rationale=match.rationale,
                            createdAt=current_date,
                        )
                        batch.save(suggestion)

            return HTTPStatus.OK, 'Suggestions saved successfully', None

        except (PynamoDBConnectionError, TableDoesNotExist) as e:
            error_msg = f'Failed to save suggestions: {str(e)}'
            self.logger.error(error_msg)
            return HTTPStatus.INTERNAL_SERVER_ERROR, None, error_msg
