from models.entity import Entities
from pydantic import BaseModel
from pynamodb.attributes import UnicodeAttribute


class ChatTopic(Entities, discriminator='CHAT_TOPIC'):
    # hk: CHAT_TOPIC#<userId>
    # rk: TOPIC#<entryId>

    title = UnicodeAttribute(null=False)


class ChatTopicIn(BaseModel):
    title: str
    userId: str
