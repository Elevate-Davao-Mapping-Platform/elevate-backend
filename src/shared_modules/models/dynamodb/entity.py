import os

from pynamodb.attributes import (
    BooleanAttribute,
    ListAttribute,
    MapAttribute,
    NumberAttribute,
    UnicodeAttribute,
)
from pynamodb.models import Model
from shared_modules.models.dynamodb.gsi import GSI1PKIndex


class LatLng(MapAttribute):
    lat = NumberAttribute()
    lng = NumberAttribute()


class Location(MapAttribute):
    address = UnicodeAttribute()
    latlng = LatLng()


class Contact(MapAttribute):
    platform = UnicodeAttribute()
    value = UnicodeAttribute()


class Milestone(MapAttribute):
    title = UnicodeAttribute()
    dateAchieved = UnicodeAttribute()
    description = UnicodeAttribute(null=True)


class Founder(MapAttribute):
    founderId = UnicodeAttribute()
    name = UnicodeAttribute()
    role = UnicodeAttribute(null=True)
    dateJoined = UnicodeAttribute(null=True)
    overview = UnicodeAttribute(null=True)
    photoObjectkey = UnicodeAttribute(null=True)
    contacts = ListAttribute(of=Contact)


class InvestmentCriteria(MapAttribute):
    criteriaName = UnicodeAttribute()
    details = UnicodeAttribute(null=True)


class PortfolioItem(MapAttribute):
    supportedStartupProject = UnicodeAttribute()
    dateSupported = UnicodeAttribute(null=True)
    isSupportingToPresent = BooleanAttribute(null=True)
    roleAndImpact = UnicodeAttribute(null=True)


class Entity(Model):
    """
    PynamoDB model for Startups and Enablers
    """

    class Meta:
        table_name = os.getenv('ENTITIES_TABLE')
        region = os.getenv('REGION')
        billing_mode = 'PAY_PER_REQUEST'

    # Primary keys
    hashKey = UnicodeAttribute(hash_key=True)  # Format: "STARTUP#id" or "ENABLER#id"
    rangeKey = UnicodeAttribute(
        range_key=True
    )  # Format: "STARTUP#METADATA", "ENABLER#CONTACTS", etc.

    # GSI
    GSI1PK = UnicodeAttribute(null=True)
    gsi1_index = GSI1PKIndex()

    # Common attributes
    email = UnicodeAttribute()
    logoObjectKey = UnicodeAttribute(null=True)
    dateFounded = UnicodeAttribute(null=True)
    description = UnicodeAttribute(null=True)
    location = Location(null=True)
    createdAt = UnicodeAttribute(null=True)
    updatedAt = UnicodeAttribute(null=True)
    contacts = ListAttribute(of=Contact, null=True)

    # Add new optional attributes
    role = UnicodeAttribute(null=True)
    visibility = BooleanAttribute(null=True)

    # Startup-specific attributes
    startUpName = UnicodeAttribute(null=True)
    startupStage = UnicodeAttribute(null=True)
    revenueModel = ListAttribute(of=UnicodeAttribute, null=True)
    industries = ListAttribute(of=UnicodeAttribute, null=True)
    milestones = ListAttribute(of=Milestone, null=True)
    founders = ListAttribute(of=Founder, null=True)

    # Enabler-specific attributes
    enablerName = UnicodeAttribute(null=True)
    organizationType = ListAttribute(of=UnicodeAttribute, null=True)
    industryFocus = ListAttribute(of=UnicodeAttribute, null=True)
    supportType = ListAttribute(of=UnicodeAttribute, null=True)
    fundingStageFocus = ListAttribute(of=UnicodeAttribute, null=True)
    investmentAmount = NumberAttribute(null=True)
    startupStagePreference = ListAttribute(of=UnicodeAttribute, null=True)
    preferredBusinessModels = ListAttribute(of=UnicodeAttribute, null=True)
    investmentCriteria = ListAttribute(of=InvestmentCriteria, null=True)
    portfolio = ListAttribute(of=PortfolioItem, null=True)

    # Saved Profile attributes
    enablerId = UnicodeAttribute(null=True)
    startupId = UnicodeAttribute(null=True)
    entityType = UnicodeAttribute(null=True)
    savedProfileId = UnicodeAttribute(null=True)
    savedProfileType = UnicodeAttribute(null=True)

    # Suggestion Attributes
    suggestionId = UnicodeAttribute(null=True)
    certainty = NumberAttribute(null=True)
    rationale = UnicodeAttribute(null=True)
    matchPairId = UnicodeAttribute(null=True)
    matchPairType = UnicodeAttribute(null=True)
    matchPairName = UnicodeAttribute(null=True)

    forSuggestionGeneration = BooleanAttribute(null=True)
