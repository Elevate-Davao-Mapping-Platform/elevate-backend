from pynamodb.attributes import UnicodeAttribute
from pynamodb.indexes import AllProjection, GlobalSecondaryIndex


class GSI1PKIndex(GlobalSecondaryIndex):
    """
    Global Secondary Index for alternative query patterns
    """

    class Meta:
        index_name = 'GSI1PK'
        projection = AllProjection()
        read_capacity_units = 1
        write_capacity_units = 1

    GSI1PK = UnicodeAttribute(hash_key=True)
    rangeKey = UnicodeAttribute(range_key=True)
