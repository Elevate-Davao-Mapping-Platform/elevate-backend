from http import HTTPStatus
from typing import List, Optional, Union

from aws_lambda_powertools import Logger
from generate_suggestions.usecases.llm_usecase import LLMUsecase
from shared_modules.models.schema.message import ErrorResponse
from shared_modules.models.schema.suggestions import SuggestionMatchList
from shared_modules.repositories.entity_repository import EntityRepository
from shared_modules.repositories.suggestion_repository import SuggestionRepository


class SuggestionUsecase:
    def __init__(self):
        self.entity_repository = EntityRepository()
        self.llm_usecase = LLMUsecase()
        self.suggestion_repository = SuggestionRepository()
        self.logger = Logger()

    def get_suggestions(
        self, entity_ids_selected: Optional[List[str]] = None
    ) -> Union[SuggestionMatchList, ErrorResponse]:
        """
        Generate a response from the LLM, ensuring all selected entities get suggestions.

        :param list entity_ids_selected: The entity IDs selected to generate a response for.
        :return Union[SuggestionMatchList, ErrorResponse]: The response from the LLM.
        """
        self.logger.debug('Getting suggestions...')
        try:
            status, entities_available, message = self.entity_repository.get_entity_list()
            if status != HTTPStatus.OK:
                return ErrorResponse(
                    response=message,
                    status=status,
                )

            entities_selected = (
                [
                    entity
                    for entity in entities_available
                    if (entity.startupId or entity.enablerId) in entity_ids_selected
                ]
                if entity_ids_selected
                else entities_available
            )

            # Track which selected entities have received suggestions
            entities_with_suggestions = set()
            all_matches = []

            # First attempt to get suggestions for all entities
            suggestions = self.llm_usecase.generate_response(entities_available, entities_selected)
            if isinstance(suggestions, ErrorResponse):
                return suggestions

            # Track which entities got suggestions in the first round
            for match in suggestions.matches:
                for entity in match.matchPair:
                    entities_with_suggestions.add(entity.entityId)

            all_matches.extend(suggestions.matches)

            # Check if any selected entities didn't get suggestions
            entities_missing_suggestions = [
                entity
                for entity in entities_selected
                if (entity.startupId or entity.enablerId) not in entities_with_suggestions
            ]

            # If there are entities missing suggestions, do another round focusing on them
            if entities_missing_suggestions:
                self.logger.info(
                    f'Generating additional suggestions for {len(entities_missing_suggestions)} entities'
                )

                # Create a new prompt focusing only on the missing entities
                suggestions = self.llm_usecase.generate_response(
                    entities_available, entities_missing_suggestions
                )
                if isinstance(suggestions, ErrorResponse):
                    return suggestions

                if not isinstance(suggestions, ErrorResponse):
                    all_matches.extend(suggestions.matches)

            return SuggestionMatchList(matches=all_matches)

        except Exception as e:
            self.logger.error(f'Error generating response: {e}')
            return ErrorResponse(
                response=str(e),
                status=HTTPStatus.INTERNAL_SERVER_ERROR,
            )
