from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.data_classes import (
    AppSyncResolverEvent,
    event_source,
)
from aws_lambda_powertools.utilities.typing import LambdaContext
from get_saved_profiles.usecases.profiles_usecase import SavedProfilesUsecase

logger = Logger()


@logger.inject_lambda_context
@event_source(data_class=AppSyncResolverEvent)
def handler(event: AppSyncResolverEvent, context: LambdaContext) -> dict:
    _ = context

    usecase = SavedProfilesUsecase()

    arguments = event.arguments
    info = event.info

    return usecase.get_saved_profiles(
        entity_type=arguments.get('entityType'),
        entity_id=arguments.get('entityId'),
        query_selection_set=info.get('selectionSetGraphQL'),
    )
