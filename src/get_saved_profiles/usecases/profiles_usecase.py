from http import HTTPStatus
from typing import List

from aws_lambda_powertools import Logger
from shared_modules.constants.entity_constants import EntityType
from shared_modules.models.schema.entity import EntitySchema
from shared_modules.repositories.entity_repository import EntityRepository
from shared_modules.repositories.profiles_repository import ProfilesRepository


class SavedProfilesUsecase:
    def __init__(self):
        self.profiles_repository = ProfilesRepository()
        self.entity_repository = EntityRepository()
        self.logger = Logger()
        self.entity_field_map = {
            EntityType.STARTUP: {
                'contacts': 'STARTUP#CONTACTS',
                'milestones': 'STARTUP#MILESTONES',
                'founders': 'STARTUP#FOUNDERS',
            },
            EntityType.ENABLER: {
                'contacts': 'ENABLER#CONTACTS',
                'investmentCriteria': 'ENABLER#INVESTMENT_CRITERIA',
                'portfolio': 'ENABLER#PORTFOLIO',
            },
        }

    def get_saved_profiles(
        self, entity_type: EntityType, entity_id: str, query_selection_set: str
    ) -> List[EntitySchema]:
        """
        Get profiles for a given entity.

        :param EntityType entity_type: The type of entity (e.g., EntityType.STARTUP or EntityType.ENABLER)
        :param str entity_id: The ID of the entity

        :return Union[List[EntitySchema], ErrorResponse]: A list of entity profiles and/or an error response
        """
        status, saved_profiles, _ = self.profiles_repository.get_saved_profiles(
            entity_type, entity_id
        )
        if status != HTTPStatus.OK:
            self.logger.error(f'Failed to get saved profiles: {status}')
            return []

        profile_item_keys = []
        for profile in saved_profiles:
            hash_key = f'{profile.savedProfileType}#{profile.savedProfileId}'
            range_key = f'{profile.savedProfileType}#METADATA'
            profile_item_keys.append((hash_key, range_key))

            entity_fields = self.entity_field_map.get(profile.savedProfileType, {})
            profile_item_keys.extend(
                (hash_key, key_suffix)
                for field, key_suffix in entity_fields.items()
                if field in query_selection_set
            )

        status, entities, _ = self.entity_repository.batch_get_entities(item_keys=profile_item_keys)
        if status != HTTPStatus.OK:
            self.logger.error(f'Failed to get entities: {status}')
            return []

        entity_data_list: List[dict] = [
            {
                '__typename': 'Startup' if entity.startupId else 'Enabler',
                **entity.model_dump(),
                'isSaved': True,
            }
            for entity in entities
        ]

        return entity_data_list
