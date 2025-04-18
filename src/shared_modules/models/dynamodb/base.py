import os

from pynamodb.attributes import DiscriminatorAttribute, UnicodeAttribute
from pynamodb.models import Model


class Entities(Model):
    class Meta:
        table_name = os.getenv('ENTITIES_TABLE')
        region = os.getenv('REGION')
        billing_mode = 'PAY_PER_REQUEST'

    cls = DiscriminatorAttribute()

    hashKey = UnicodeAttribute(hash_key=True)
    rangeKey = UnicodeAttribute(range_key=True)

    createdAt = UnicodeAttribute(null=True)
    updatedAt = UnicodeAttribute(null=True)
