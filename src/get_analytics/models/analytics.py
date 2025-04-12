from decimal import Decimal
from typing import Any, List, Optional

from pydantic import BaseModel, Field, field_validator


class InvestorEngagementData(BaseModel):
    year: str = Field(..., description='Year of the engagement data')
    month: str = Field(..., description='Month of the engagement data in YYYY-MM format')
    responded: float = Field(
        ..., description='Percentage of investors who responded to startup matches'
    )
    ignored: float = Field(..., description='Percentage of investors who ignored startup matches')

    @field_validator('responded', 'ignored', mode='before')
    @classmethod
    def round_decimal(cls, value: Any) -> Any:
        if isinstance(value, (float, str, Decimal)):
            return round(float(value), 2)
        return value


class MatchConfidenceData(BaseModel):
    year: str = Field(..., description='Year of the match confidence data')
    month: str = Field(..., description='Month of the match confidence data')
    confidence: Decimal = Field(..., decimal_places=2, description='AI match confidence score')
    threshold: Decimal = Field(
        ..., decimal_places=2, description='Confidence threshold used for matching'
    )

    @field_validator('confidence', 'threshold', mode='before')
    @classmethod
    def round_decimal(cls, value: Any) -> Any:
        if isinstance(value, (float, str, Decimal)):
            return round(float(value), 2)
        return value


class StartupEngagementData(BaseModel):
    year: str = Field(..., description='Year of the engagement data')
    month: str = Field(..., description='Month of the engagement data in YYYY-MM format')
    responded: Decimal = Field(
        ..., decimal_places=2, description='Percentage of startups that responded to the matches'
    )
    ignored: Decimal = Field(
        ..., decimal_places=2, description='Percentage of startups that ignored the matches'
    )

    @field_validator('responded', 'ignored', mode='before')
    @classmethod
    def round_decimal(cls, value: Any) -> Any:
        if isinstance(value, (float, str, Decimal)):
            return round(float(value), 2)
        return value


class StartupMaturityData(BaseModel):
    stage: str = Field(..., description='Startup maturity/funding stage')
    count: int = Field(..., description='Number of startups in this stage')


class InvestorRecommendation(BaseModel):
    name: Optional[str] = Field(None, description='Name of the recommended investor (if available)')
    confidence: str = Field(
        ..., description='Confidence level of the recommendation (e.g. High, Medium, Low)'
    )
    score: Decimal = Field(
        ..., decimal_places=2, description='Numerical confidence score for the recommendation'
    )

    @field_validator('score', mode='before')
    @classmethod
    def round_decimal(cls, value: Any) -> Any:
        if isinstance(value, (float, str, Decimal)):
            return round(float(value), 2)
        return value


class Analytics(BaseModel):
    matchConfidence: List[MatchConfidenceData] = Field(
        ..., description='Historical data of AI match confidence scores'
    )

    # startup analytics
    investorEngagement: Optional[List[InvestorEngagementData]] = Field(
        default=None, description='Data about how investors engage with startup matches'
    )
    topInvestorRecommendations: Optional[List[InvestorRecommendation]] = Field(
        default=None, description='List of top recommended investors'
    )

    # enabler analytics
    startupEngagement: Optional[List[StartupEngagementData]] = Field(
        default=None, description='Historical accuracy data of startup matches'
    )
    startupMaturity: Optional[List[StartupMaturityData]] = Field(
        default=None, description='Distribution of startups across different maturity stages'
    )
