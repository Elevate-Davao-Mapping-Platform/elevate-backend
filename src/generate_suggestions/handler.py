from aws_lambda_powertools import Logger
from generate_suggestions.controllers.suggestions_controller import (
    SuggestionsController,
)

logger = Logger()


@logger.inject_lambda_context
def handler(event, context):
    _, _ = event, context

    suggestions_controller = SuggestionsController()

    response = suggestions_controller.get_suggestions()
    return response
