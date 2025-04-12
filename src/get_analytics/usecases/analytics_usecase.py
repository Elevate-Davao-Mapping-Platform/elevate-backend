from datetime import datetime
from http import HTTPStatus

from get_analytics.constants.analytics_constants import (
    AnalyticsConstants,
    InvestorRecommendationConstants,
)
from get_analytics.models.analytics import (
    Analytics,
    InvestorEngagementData,
    InvestorRecommendation,
    MatchConfidenceData,
    StartupEngagementData,
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
        monthly_confidence_map = {}

        top_investor_recommendations_list = []
        top_investor_recommendations_confidence = []

        investor_engagement_map = {}
        startup_engagement_map = {}

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

            date_obj = datetime.fromisoformat(suggestion.createdAt.replace('Z', '+00:00'))
            month = date_obj.strftime('%m')
            year = date_obj.strftime('%Y')

            year_month_id = f'{year}-{month}'

            # ======================
            # Match Confidence
            # ======================
            if year_month_id not in monthly_confidence_map:
                monthly_confidence_map[year_month_id] = []

            monthly_confidence_map[year_month_id].append(suggestion.certainty)

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

            # ======================
            # Investor Engagement
            # ======================
            if entity_type == EntityType.STARTUP:
                if year_month_id not in investor_engagement_map:
                    investor_engagement_map[year_month_id] = {
                        'responded': 0,
                        'ignored': 0,
                    }

                if suggestion.isSaved:
                    investor_engagement_map[year_month_id]['responded'] += 1
                else:
                    investor_engagement_map[year_month_id]['ignored'] += 1

            # ======================
            # Startup Engagement
            # ======================
            if entity_type == EntityType.ENABLER and suggestion.matchPairType == EntityType.STARTUP:
                if year_month_id not in startup_engagement_map:
                    startup_engagement_map[year_month_id] = {
                        'responded': 0,
                        'ignored': 0,
                    }

                if suggestion.isSaved:
                    startup_engagement_map[year_month_id]['responded'] += 1
                else:
                    startup_engagement_map[year_month_id]['ignored'] += 1

        # Calculate average confidence for each month
        for year_month_id, confidences in monthly_confidence_map.items():
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

        investor_engagement = []
        for year_month_id, engagement_data in investor_engagement_map.items():
            year, month = year_month_id.split('-')
            investor_engagement.append(
                InvestorEngagementData(
                    year=year,
                    month=month,
                    responded=engagement_data['responded'],
                    ignored=engagement_data['ignored'],
                )
            )

        startup_engagement = []
        for year_month_id, engagement_data in startup_engagement_map.items():
            year, month = year_month_id.split('-')
            startup_engagement.append(
                StartupEngagementData(
                    year=year,
                    month=month,
                    responded=engagement_data['responded'],
                    ignored=engagement_data['ignored'],
                )
            )

        return Analytics(
            matchConfidence=match_confidence,
            investorEngagement=investor_engagement,
            topInvestorRecommendations=top_investor_recommendations_list,
            startupEngagement=startup_engagement,
            startupMaturity=startup_maturity,
        )
