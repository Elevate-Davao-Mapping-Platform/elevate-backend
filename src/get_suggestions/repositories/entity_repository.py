import os
from http import HTTPStatus
from typing import List, Tuple

from aws_lambda_powertools import Logger
from pynamodb.connection import Connection
from pynamodb.exceptions import GetError, PynamoDBConnectionError, TableDoesNotExist
from shared_modules.models.dynamodb.entity import Entity
from shared_modules.models.schema.entity import EntitySchema


class EntityRepository:
    def __init__(self) -> None:
        self.conn = Connection(region=os.getenv('REGION'))
        self.logger = Logger()

    def batch_get_entities_with_suggestions(
        self, suggestion_item_keys: List[Tuple[str, str]]
    ) -> Tuple[HTTPStatus, List[EntitySchema], str]:
        """Get a list of all entities (Entity and/or enablers)

        :param suggestion_item_keys: List of suggestion item keys
        :type suggestion_item_keys: List[Tuple[str, str]]

        :return: Tuple containing HTTP status, list of entity profiles, and a message
        :rtype: Tuple[HTTPStatus, List[EntitySchema], str]
        """
        try:
            entities: List[Entity] = Entity.batch_get(suggestion_item_keys)
            processed_entities = []
            entity_id_to_entity_map = {}

            # Process all entities, regardless of order
            for entity in entities:
                hash_key = entity.hashKey
                entity_type = hash_key.split('#')[0]
                entity_id = hash_key.split('#')[1]
                range_key = entity.rangeKey
                entity_dict = entity.to_simple_dict()

                # Get or create entity object from map
                if entity_id not in entity_id_to_entity_map:
                    entity_id_to_entity_map[entity_id] = {
                        'startupId' if entity_type == 'STARTUP' else 'enablerId': entity_id,
                        '__typename': 'Startup' if entity_type == 'STARTUP' else 'Enabler',
                    }

                current_entity = entity_id_to_entity_map[entity_id]

                # Add item data based on rangeKey and entity type
                if entity_type == 'STARTUP':
                    if range_key == 'STARTUP#METADATA':
                        current_entity.update(
                            {
                                'startUpName': entity.startUpName,
                                'email': entity.email,
                                'logoObjectKey': entity.logoObjectKey,
                                'dateFounded': entity.dateFounded,
                                'startupStage': entity.startupStage,
                                'description': entity.description,
                                'location': entity_dict.get('location'),
                                'revenueModel': entity.revenueModel,
                                'createdAt': entity.createdAt,
                                'industries': entity.industries,
                            }
                        )
                    elif range_key == 'STARTUP#CONTACTS':
                        current_entity['contacts'] = entity_dict['contacts']
                    elif range_key == 'STARTUP#MILESTONES':
                        current_entity['milestones'] = entity_dict['milestones']
                    elif range_key == 'STARTUP#FOUNDERS':
                        current_entity['founders'] = entity_dict['founders']

                elif entity_type == 'ENABLER':
                    if range_key == 'ENABLER#METADATA':
                        current_entity.update(
                            {
                                'enablerName': entity.enablerName,
                                'email': entity.email,
                                'logoObjectKey': entity.logoObjectKey,
                                'dateFounded': entity.dateFounded,
                                'organizationType': entity.organizationType,
                                'description': entity.description,
                                'location': entity_dict.get('location'),
                                'industryFocus': entity.industryFocus,
                                'supportType': entity.supportType,
                                'fundingStageFocus': entity.fundingStageFocus,
                                'investmentAmount': entity.investmentAmount,
                                'startupStagePreference': entity.startupStagePreference,
                                'preferredBusinessModels': entity.preferredBusinessModels,
                            }
                        )
                    elif range_key == 'ENABLER#CONTACTS':
                        current_entity['contacts'] = entity_dict['contacts']
                    elif range_key == 'ENABLER#INVESTMENT_CRITERIA':
                        current_entity['investmentCriteria'] = entity_dict['investmentCriteria']
                    elif range_key == 'ENABLER#PORTFOLIO':
                        current_entity['portfolio'] = entity_dict['portfolio']

            # Convert all entities in the map to EntitySchema objects
            processed_entities = [
                EntitySchema(**entity_data) for entity_data in entity_id_to_entity_map.values()
            ]

            return HTTPStatus.OK, processed_entities, 'Success'

        except GetError as e:
            self.logger.error(f'Error getting entities: {e}')
            return HTTPStatus.INTERNAL_SERVER_ERROR, [], str(e)

        except PynamoDBConnectionError as e:
            self.logger.error(f'Error connecting to DynamoDB: {e}')
            return HTTPStatus.INTERNAL_SERVER_ERROR, [], str(e)

        except TableDoesNotExist as e:
            self.logger.error(f'Table does not exist: {e}')
            return HTTPStatus.INTERNAL_SERVER_ERROR, [], str(e)
