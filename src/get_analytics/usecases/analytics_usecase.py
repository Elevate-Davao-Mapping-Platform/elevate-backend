from datetime import datetime
from http import HTTPStatus

from get_analytics.constants.analytics_constants import (
    AnalyticsConstants,
    InvestorRecommendationConstants,
)
from get_analytics.models.analytics import (
    Analytics,
    InvestorRecommendation,
    MatchConfidenceData,
    StartupMaturityData,
)
from shared_modules.constants.entity_constants import EntityType
from shared_modules.models.schema.entity import EntitySchema
from shared_modules.models.schema.message import ErrorResponse
from shared_modules.repositories.entity_repository import EntityRepository
from shared_modules.repositories.suggestion_repository import SuggestionRepository


class AnalyticsUsecase:
    def __init__(self):
        self.entity_repository = EntityRepository()
        self.suggestion_repository = SuggestionRepository()

    def get_analytics(self, entity_type: EntityType, entity_id: str) -> Analytics:
        """
        Get analytics for a given entity.

        :param EntityType entity_type: The type of entity (e.g., EntityType.STARTUP or EntityType.ENABLER)
        :param str entity_id: The ID of the entity

        :return Analytics: The analytics for the given entity
        """
        match_confidence = []
        investor_engagement = []

        monthly_confidence = {}

        top_investor_recommendations_list = []
        top_investor_recommendations_confidence = []

        startup_engagement = []

        startup_maturity_count_map = {}

        status, suggestions, message = self.suggestion_repository.get_suggestions(
            entity_type, entity_id
        )
        if status != HTTPStatus.OK:
            return ErrorResponse(
                response=message,
                status=status,
            )

        for suggestion in suggestions:
            status, entity_list, message = self.entity_repository.batch_get_entities(
                [(suggestion.matchPairId, f'{suggestion.matchPairType}#METADATA')]
            )
            if status != HTTPStatus.OK or not entity_list:
                return ErrorResponse(
                    response=message,
                    status=status,
                )

            entity: EntitySchema = entity_list[0]

            # ======================
            # Match Confidence
            # ======================
            date_obj = datetime.fromisoformat(suggestion.createdAt.replace('Z', '+00:00'))
            month = date_obj.strftime('%m')
            year = date_obj.strftime('%Y')

            year_month_id = f'{year}-{month}'

            if year_month_id not in monthly_confidence:
                monthly_confidence[year_month_id] = []

            monthly_confidence[year_month_id].append(suggestion.certainty)

            # ======================
            # Top Investor Recommendations
            # ======================
            if suggestion.matchPairType == EntityType.ENABLER and (
                len(top_investor_recommendations_list) < 5
                or suggestion.certainty > min(top_investor_recommendations_confidence)
            ):
                score = suggestion.certainty * 100
                name = entity.enablerName or entity.startUpName
                recommendation = InvestorRecommendation(
                    name=name,
                    confidence=InvestorRecommendationConstants.get_confidence_threshold(
                        suggestion.certainty
                    ),
                    score=score,
                )
                top_investor_recommendations_list.append(recommendation)
                top_investor_recommendations_confidence.append(suggestion.certainty)

                if len(top_investor_recommendations_list) > 5:
                    top_investor_recommendations_list.pop(0)
                    top_investor_recommendations_confidence.pop(0)

            # ======================
            # Startup Maturity
            # ======================
            if suggestion.matchPairType == EntityType.STARTUP:
                funding_stage = entity.startupStage
                startup_maturity_count_map[funding_stage] = (
                    startup_maturity_count_map.get(funding_stage, 0) + 1
                )

        # Calculate average confidence for each month
        for year_month_id, confidences in monthly_confidence.items():
            avg_confidence = sum(confidences) * 100 / len(confidences)
            year, month = year_month_id.split('-')
            match_confidence.append(
                MatchConfidenceData(
                    year=year,
                    month=month,
                    confidence=avg_confidence,
                    threshold=AnalyticsConstants.MATCH_CONFIDENCE_THRESHOLD,
                )
            )

        match_confidence.sort(key=lambda x: x.year)
        match_confidence.sort(key=lambda x: x.month)

        startup_maturity = [
            StartupMaturityData(stage=funding_stage, count=count)
            for funding_stage, count in startup_maturity_count_map.items()
        ]

        return Analytics(
            matchConfidence=match_confidence,
            investorEngagement=investor_engagement,
            topInvestorRecommendations=top_investor_recommendations_list,
            startupEngagement=startup_engagement,
            startupMaturity=startup_maturity,
        )
