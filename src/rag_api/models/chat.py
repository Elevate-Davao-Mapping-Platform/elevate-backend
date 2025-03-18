from typing import Optional

from models.entity import Entities
from pydantic import BaseModel
from pynamodb.attributes import UnicodeAttribute


class Chat(Entities, discriminator='Chat'):
    # hk: CHAT#<userId>TOPIC#<chatTopicId>
    # rk: MESSAGE#<entryId>

    message = UnicodeAttribute(null=False)
    type = UnicodeAttribute(null=False)
    userId = UnicodeAttribute(null=False)
    chatTopicId = UnicodeAttribute(null=False)


class ChatIn(BaseModel):
    message: str
    type: str
    userId: str
    chatTopicId: str


class ChatPromptIn(BaseModel):
    query: str
    userId: str
    chatTopicId: Optional[str] = None


class ChatOut(BaseModel):
    response: str
    chatTopicId: str
    userId: str
    chatId: str
