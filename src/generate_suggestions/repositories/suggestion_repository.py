import os
from datetime import datetime
from http import HTTPStatus
from typing import Tuple
from uuid import uuid4

import pytz
from aws_lambda_powertools import Logger
from pynamodb.connection import Connection
from pynamodb.exceptions import PynamoDBConnectionError, TableDoesNotExist
from shared_modules.models.dynamodb.suggestions import Suggestions
from shared_modules.models.schema.suggestions import SuggestionMatchList


class SuggestionRepository:
    def __init__(self):
        self.conn = Connection(region=os.getenv('REGION'))
        self.logger = Logger()

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
