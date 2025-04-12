from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.data_classes import EventBridgeEvent, event_source
from aws_lambda_powertools.utilities.typing import LambdaContext
from generate_suggestions.controllers.suggestions_controller import (
    SuggestionsController,
)

logger = Logger()


@logger.inject_lambda_context
@event_source(data_class=EventBridgeEvent)
def handler(event: EventBridgeEvent, context: LambdaContext) -> dict:
    _, _ = event, context

    suggestions_controller = SuggestionsController()
    return suggestions_controller.get_suggestions()
