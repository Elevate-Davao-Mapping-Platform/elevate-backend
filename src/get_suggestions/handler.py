from aws_lambda_powertools import Logger
from get_suggestions.usecases.suggestions_usecase import SuggestionsUsecase

logger = Logger()


@logger.inject_lambda_context
def handler(event, context):
    _ = context

    usecase = SuggestionsUsecase()

    arguments = event['arguments']
    info = event['info']

    response = usecase.get_suggestions(
        entity_type=arguments.get('entityType'),
        entity_id=arguments.get('entityId'),
        query_selection_set=info.get('selectionSetGraphQL'),
    )

    return response
