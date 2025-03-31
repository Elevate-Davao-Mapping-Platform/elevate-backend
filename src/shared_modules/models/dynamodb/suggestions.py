from pynamodb.attributes import NumberAttribute, UnicodeAttribute
from shared_modules.models.dynamodb.base import Entities


class Suggestions(Entities, discriminator='Suggestion'):
    """
    Suggestions are entities that are used to suggest matches between startups and enablers.

    hk: STARTUP#<startupId> or ENABLER#<enablerId>
    rk: STARTUP#SUGGESTION#STARTUP#{suggestionId}
        or STARTUP#SUGGESTION#ENABLER#{suggestionId}
        or ENABLER#SUGGESTION#ENABLER#{suggestionId}
    """

    suggestionId = UnicodeAttribute(null=False)
    certainty = NumberAttribute(null=False)
    rationale = UnicodeAttribute(null=False)
    matchPairId = UnicodeAttribute(null=False)
