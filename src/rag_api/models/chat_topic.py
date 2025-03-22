from pydantic import BaseModel
from pynamodb.attributes import UnicodeAttribute
from rag_api.models.entity import Entities


class ChatTopic(Entities, discriminator='CHAT_TOPIC'):
    # hk: CHAT_TOPIC#<userId>
    # rk: TOPIC#<entryId>

    title = UnicodeAttribute(null=False)


class ChatTopicIn(BaseModel):
    title: str
    userId: str
