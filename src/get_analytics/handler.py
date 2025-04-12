from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.data_classes import (
    AppSyncResolverEvent,
    event_source,
)
from aws_lambda_powertools.utilities.typing import LambdaContext
from get_analytics.usecases.analytics_usecase import AnalyticsUsecase

logger = Logger()


@logger.inject_lambda_context
@event_source(data_class=AppSyncResolverEvent)
def handler(event: AppSyncResolverEvent, context: LambdaContext) -> dict:
    _ = context

    usecase = AnalyticsUsecase()

    arguments = event.arguments

    response = usecase.get_analytics(
        entity_type=arguments.get('entityType'),
        entity_id=arguments.get('entityId'),
    )

    return response.model_dump()
