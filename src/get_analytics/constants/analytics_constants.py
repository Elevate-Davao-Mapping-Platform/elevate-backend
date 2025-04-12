from enum import Enum


class InvestorRecommendationConstants(Enum):
    HIGH = 'HIGH'
    MEDIUM = 'MEDIUM'
    LOW = 'LOW'

    HIGH_CONFIDENCE_THRESHOLD = 0.8
    MEDIUM_CONFIDENCE_THRESHOLD = 0.5
    LOW_CONFIDENCE_THRESHOLD = 0.2

    @classmethod
    def get_confidence_threshold(cls, confidence: float) -> str:
        if confidence >= cls.HIGH_CONFIDENCE_THRESHOLD.value:
            return cls.HIGH.value
        elif confidence >= cls.MEDIUM_CONFIDENCE_THRESHOLD.value:
            return cls.MEDIUM.value
        else:
            return cls.LOW.value


class AnalyticsConstants:
    MATCH_CONFIDENCE_THRESHOLD = 70
