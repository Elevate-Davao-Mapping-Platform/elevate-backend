from http import HTTPStatus
from typing import List

from get_suggestions.repositories.entity_repository import EntityRepository
from get_suggestions.repositories.suggestion_repository import SuggestionRepository
from shared_modules.constants.entity_constants import EntityType
from shared_modules.models.schema.entity import EntitySchema


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

        suggestion_item_keys = []
        for suggestion in suggestions:
            suggestion_item_keys.append(
                (suggestion.matchPairId, f'{suggestion.matchPairType}#METADATA')
            )
            # Add requested fields based on entity type
            entity_fields = self.entity_field_map.get(suggestion.matchPairType, {})
            for field, key_suffix in entity_fields.items():
                if field in query_selection_set:
                    suggestion_item_keys.append((suggestion.matchPairId, key_suffix))

        status, entities, _ = self.entity_repository.batch_get_entities_with_suggestions(
            suggestion_item_keys
        )
        if status != HTTPStatus.OK:
            return []

        entity_data = [
            {**entity.model_dump(), '__typename': 'Startup' if entity.startupId else 'Enabler'}
            for entity in entities
        ]

        return entity_data
