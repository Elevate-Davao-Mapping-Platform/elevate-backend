from http import HTTPStatus
from typing import Union

from aws_lambda_powertools import Logger
from generate_suggestions.repositories.entity_repository import EntityRepository
from generate_suggestions.repositories.suggestion_repository import SuggestionRepository
from generate_suggestions.usecases.llm_usecase import LLMUsecase
from shared_modules.models.schema.message import ErrorResponse
from shared_modules.models.schema.suggestions import SuggestionMatchList


class SuggestionUsecase:
    def __init__(self):
        self.entity_repository = EntityRepository()
        self.llm_usecase = LLMUsecase()
        self.suggestion_repository = SuggestionRepository()
        self.logger = Logger()

    def get_suggestions(self) -> Union[SuggestionMatchList, ErrorResponse]:
        self.logger.info('Getting suggestions')

        status, entity_list, message = self.entity_repository.get_entity_list()
        if status != HTTPStatus.OK:
            return ErrorResponse(
                response=message,
                status=status,
            )

        suggestions = self.llm_usecase.generate_response(entity_list)
        if isinstance(suggestions, ErrorResponse):
            return suggestions

        self.logger.info(f'Saving suggestions: {suggestions}')

        status, message, error = self.suggestion_repository.save_suggestions(suggestions)
        if status != HTTPStatus.OK:
            return ErrorResponse(
                response=error,
                status=status,
            )

        self.logger.info('Suggestions saved successfully')
        return suggestions
