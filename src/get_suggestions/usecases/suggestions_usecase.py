from http import HTTPStatus
from typing import List

from shared_modules.constants.entity_constants import EntityType
from shared_modules.models.schema.entity import EntitySchema
from shared_modules.repositories.entity_repository import EntityRepository
from shared_modules.repositories.suggestion_repository import SuggestionRepository


class SuggestionsUsecase:
    def __init__(self):
        self.suggestion_repository = SuggestionRepository()
        self.entity_repository = EntityRepository()
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

    def get_suggestions(
        self, entity_type: EntityType, entity_id: str, query_selection_set: str
    ) -> List[EntitySchema]:
        """
        Get suggestions for a given entity.

        :param EntityType entity_type: The type of entity (e.g., EntityType.STARTUP or EntityType.ENABLER)
        :param str entity_id: The ID of the entity

        :return Union[List[EntitySchema], ErrorResponse]: A list of entity profiles and/or an error response
        """
        status, suggestions, _ = self.suggestion_repository.get_suggestions(entity_type, entity_id)
        if status != HTTPStatus.OK:
            return []

        is_saved_map = {}

        suggestion_item_keys = []
        for suggestion in suggestions:
            suggestion_item_keys.append(
                (suggestion.matchPairId, f'{suggestion.matchPairType}#METADATA')
            )

            match_entity_id = suggestion.matchPairId.split('#')[1]
            is_saved_map[match_entity_id] = suggestion.isSaved or False

            # Add requested fields based on entity type
            entity_fields = self.entity_field_map.get(suggestion.matchPairType, {})
            suggestion_item_keys.extend(
                (suggestion.matchPairId, key_suffix)
                for field, key_suffix in entity_fields.items()
                if field in query_selection_set
            )

        status, entities, _ = self.entity_repository.batch_get_entities(
            item_keys=suggestion_item_keys
        )
        if status != HTTPStatus.OK:
            return []

        entity_data_list: List[dict] = [
            {
                '__typename': 'Startup' if entity.startupId else 'Enabler',
                'isSaved': is_saved_map[entity.startupId]
                if entity.startupId
                else is_saved_map[entity.enablerId],
                **entity.model_dump(),
            }
            for entity in entities
        ]

        return entity_data_list
