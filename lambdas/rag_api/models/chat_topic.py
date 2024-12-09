from models.entity import Entities
from pydantic import BaseModel
from pynamodb.attributes import UnicodeAttribute


class ChatTopic(Entities, discriminator='ChatTopic'):
    # hk: ChatTopic#<userId>
    # rk: v<version_number>#<entryId>

    title = UnicodeAttribute(null=False)


class ChatTopicIn(BaseModel):
    title: str
    userId: str
