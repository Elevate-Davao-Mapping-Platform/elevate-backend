import logging
import os
import sys

from aws_lambda_powertools import Logger
from generate_suggestions.usecases.suggestion_usecase import SuggestionUsecase


class SuggestionsController:
    def __init__(self):
        self.logger = Logger()
        self.suggestion_usecase = SuggestionUsecase()

        is_local = os.getenv('IS_LOCAL')
        if is_local:
            logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
            logging.getLogger().addHandler(logging.StreamHandler(stream=sys.stdout))

    def get_suggestions(self):
        suggestions = self.suggestion_usecase.get_suggestions()
        return suggestions.model_dump()
