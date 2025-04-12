from pprint import pprint

from dotenv import load_dotenv
from shared_modules.constants.entity_constants import EntityType

load_dotenv()

from get_analytics.usecases.analytics_usecase import AnalyticsUsecase  # noqa: E402


def main():
    usecase = AnalyticsUsecase()
    response = usecase.get_analytics(
        entity_type=EntityType.STARTUP,
        entity_id='80555af4-e4f6-4068-bd5b-bedafb27d2bb',
    )
    pprint(response.model_dump_json(indent=4))


if __name__ == '__main__':
    main()
