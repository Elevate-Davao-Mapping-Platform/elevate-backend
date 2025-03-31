from aws_lambda_powertools import Logger
from get_suggestions.usecases.suggestions_usecase import SuggestionsUsecase

logger = Logger()


@logger.inject_lambda_context
def handler(event, context):
    _ = context

    usecase = SuggestionsUsecase()

    arguments = event['arguments']

    response = usecase.get_suggestions(
        entity_type=arguments.get('entityType'),
        entity_id=arguments.get('entityId'),
    )

    return response
