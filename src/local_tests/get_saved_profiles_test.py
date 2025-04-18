from dotenv import load_dotenv

load_dotenv()

from get_saved_profiles.usecases.profiles_usecase import (  # noqa: E402
    SavedProfilesUsecase,
)
from shared_modules.constants.entity_constants import EntityType  # noqa: E402


def main():
    entity_type = EntityType.STARTUP
    entity_id = '80555af4-e4f6-4068-bd5b-bedafb27d2bb'
    query_selection_set = '{\n  ... on Startup {\n    startupId\n    startUpName\n    logoObjectKey\n    dateFounded\n    industries\n    startupStage\n    description\n    revenueModel\n    createdAt\n    email\n    location {\n      address\n      latlng {\n        lat\n        lng\n      }\n    }\n    contacts {\n      platform\n      value\n    }\n    milestones {\n      title\n      dateAchieved\n      description\n    }\n    founders {\n      founderId\n      name\n      role\n      dateJoined\n      overview\n      photoObjectkey\n    }\n  }\n  ... on Enabler {\n    enablerId\n    enablerName\n    email\n    logoObjectKey\n    dateFounded\n    organizationType\n    description\n    industryFocus\n    supportType\n    fundingStageFocus\n    investmentAmount\n    startupStagePreference\n    preferredBusinessModels\n    createdAt\n    investmentCriteria {\n      criteriaName\n      details\n    }\n    portfolio {\n      supportedStartupProject\n      dateSupported\n      isSupportingToPresent\n      roleAndImpact\n    }\n    location {\n      address\n      latlng {\n        lat\n        lng\n      }\n    }\n  }\n}'
    usecase = SavedProfilesUsecase()
    response = usecase.get_saved_profiles(entity_type, entity_id, query_selection_set)
    print(response)


if __name__ == '__main__':
    main()
