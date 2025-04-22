from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.typing import LambdaContext
from generate_suggestions.controllers.suggestions_controller import (
    SuggestionsController,
)

logger = Logger()


@logger.inject_lambda_context
def handler(event: dict, context: LambdaContext) -> dict:
    _, _ = event, context

    entity_id = event.get('prev', {}).get('result', {}).get('id')
    entity_id_list = [entity_id] if entity_id else None

    suggestions_controller = SuggestionsController()
    return suggestions_controller.get_suggestions(entity_id_list)
