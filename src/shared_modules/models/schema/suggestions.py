from typing import List

from pydantic import BaseModel, Field
from shared_modules.constants.entity_constants import EntityType


class SuggestionsDBIn(BaseModel):
    suggestionId: str = Field(..., description='The ID of the suggestion')
    certainty: float = Field(..., description='The certainty of the suggestion')
    rationale: str = Field(..., description='The rationale of the suggestion')
    matchPairId: str = Field(..., description='The ID of the match pair')


class MatchedEntity(BaseModel):
    entityId: str = Field(
        ...,
        description='The unique identifier of the entity (startupId or enablerId) that will be used to look up additional details',
    )
    entityType: EntityType = Field(..., description='The type of the entity (STARTUP or ENABLER)')
    name: str = Field(
        ...,
        description='The display name of the entity (startUpName or enablerName) that will be shown in the match results',
    )


class SuggestionMatch(BaseModel):
    matchPair: List[MatchedEntity] = Field(
        ...,
        max_length=2,
        min_length=2,
        description='A pair of entities that are suggested matches. Must contain exactly 2 entities representing either startup-startup, startup-enabler, or enabler-enabler matches',
    )
    certainty: float = Field(
        ...,
        description='A confidence score between 0 and 1 indicating how strong the match is based on the analysis of compatibility factors like industry alignment, stage fit, etc.',
    )
    rationale: str = Field(
        ...,
        description='A detailed explanation of why these entities are a good match, including specific compatibility points, potential synergies, and suggested collaboration opportunities',
    )


class SuggestionMatchList(BaseModel):
    matches: List[SuggestionMatch] = Field(
        ...,
        description='An ordered list of suggested matches, sorted by certainty score from highest to lowest. Each match contains the pair of entities and detailed rationale for the suggestion',
    )
