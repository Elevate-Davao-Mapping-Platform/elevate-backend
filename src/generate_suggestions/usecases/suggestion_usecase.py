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
        self.logger.debug(
            {
                'message': 'Starting suggestion generation',
                'entity_ids_selected': entity_ids_selected,
            }
        )

        try:
            status, entities_available, entities, message = self.entity_repository.get_entity_list()
            if status != HTTPStatus.OK:
                self.logger.warning(
                    {
                        'message': 'Failed to get entity list',
                        'status': status,
                        'error_message': message,
                    }
                )
                return ErrorResponse(
                    response=message,
                    status=status,
                )

            self.logger.info(
                {
                    'message': 'Successfully retrieved entity list',
                    'entities_available_count': len(entities_available),
                }
            )

            entities_selected = []
            selected_entity_hash_key = []
            for entity in entities_available:
                is_in_selected_entity_list = (
                    entity_ids_selected
                    and (entity.startupId or entity.enablerId) in entity_ids_selected
                )
                entity_list_not_provided = not entity_ids_selected

                is_add_to_entities_selected = (
                    entity_list_not_provided or is_in_selected_entity_list
                ) and entity.forSuggestionGeneration

                if is_add_to_entities_selected:
                    entities_selected.append(entity)
                    selected_entity_hash_key.append(entity.hashKey)

            if not entities_selected:
                self.logger.error(
                    {
                        'message': 'No entities selected',
                    }
                )
                return ErrorResponse(
                    response='No entities selected',
                    status=HTTPStatus.BAD_REQUEST,
                )

            self.logger.info(
                {
                    'message': 'Filtered selected entities',
                    'entities_selected_count': len(entities_selected),
                }
            )

            # Track which selected entities have received suggestions
            entities_with_suggestions = set()
            all_matches = []

            # First attempt to get suggestions for all entities
            self.logger.debug('Generating initial suggestions for all entities')
            suggestions = self.llm_usecase.generate_response(entities_available, entities_selected)
            if isinstance(suggestions, ErrorResponse):
                self.logger.warning(
                    {
                        'message': 'Failed to generate initial suggestions',
                        'error': suggestions.response,
                    }
                )
                return suggestions

            # Track which entities got suggestions in the first round
            for match in suggestions.matches:
                for entity in match.matchPair:
                    entities_with_suggestions.add(entity.entityId)

            all_matches.extend(suggestions.matches)

            self.logger.info(
                {
                    'message': 'Initial suggestions generated',
                    'entities_with_suggestions_count': len(entities_with_suggestions),
                    'matches_generated': len(suggestions.matches),
                }
            )

            # Check if any selected entities didn't get suggestions
            entities_missing_suggestions = [
                entity
                for entity in entities_selected
                if (entity.startupId or entity.enablerId) not in entities_with_suggestions
            ]

            # If there are entities missing suggestions, do another round focusing on them
            if entities_missing_suggestions:
                self.logger.info(
                    {
                        'message': 'Generating additional suggestions for missing entities',
                        'missing_entities_count': len(entities_missing_suggestions),
                    }
                )

                # Create a new prompt focusing only on the missing entities
                suggestions = self.llm_usecase.generate_response(
                    entities_available, entities_missing_suggestions
                )
                if isinstance(suggestions, ErrorResponse):
                    self.logger.warning(
                        {
                            'message': 'Failed to generate additional suggestions',
                            'error': suggestions.response,
                        }
                    )
                    return suggestions

                if not isinstance(suggestions, ErrorResponse):
                    additional_matches = len(suggestions.matches)
                    all_matches.extend(suggestions.matches)
                    self.logger.info(
                        {
                            'message': 'Additional suggestions generated successfully',
                            'additional_matches_count': additional_matches,
                        }
                    )

            final_response = SuggestionMatchList(matches=all_matches)

            status, message = self.suggestion_repository.save_suggestions(final_response)
            if status != HTTPStatus.OK:
                self.logger.warning({'message': 'Failed to save suggestions', 'error': message})
                return ErrorResponse(
                    response=message,
                    status=status,
                )

            entity_models_selected = []
            for entity_model in entities:
                if entity_model.hashKey and entity_model.hashKey in selected_entity_hash_key:
                    entity_models_selected.append(entity_model)

            status, message = self.entity_repository.update_entity_for_suggestion_generation(
                entity_list=entity_models_selected, update_value=False
            )
            if status != HTTPStatus.OK:
                self.logger.error(
                    {
                        'message': 'Failed to update entity for suggestion generation',
                        'error': message,
                    }
                )
                return ErrorResponse(
                    response=message,
                    status=status,
                )

            self.logger.info(
                {
                    'message': 'Suggestion generation completed successfully',
                    'total_matches_count': len(all_matches),
                }
            )
            return final_response

        except Exception as e:
            self.logger.error(
                {
                    'message': 'Error generating suggestions',
                    'error': str(e),
                    'entity_ids_selected': entity_ids_selected,
                },
                exc_info=True,
            )
            return ErrorResponse(
                response=str(e),
                status=HTTPStatus.INTERNAL_SERVER_ERROR,
            )
