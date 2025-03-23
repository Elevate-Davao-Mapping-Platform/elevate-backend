from typing import Optional

from pydantic import BaseModel, Field
from pynamodb.attributes import UnicodeAttribute
from rag_api.models.entity import Entities


class Chat(Entities, discriminator='Chat'):
    # hk: CHAT#<userId>TOPIC#<chatTopicId>
    # rk: MESSAGE#<entryId>

    message = UnicodeAttribute(null=False)
    type = UnicodeAttribute(null=False)
    userId = UnicodeAttribute(null=False)
    chatTopicId = UnicodeAttribute(null=False)


class ChatIn(BaseModel):
    message: str = Field(..., description='The message to send')
    type: str = Field(..., description='The type of message')
    userId: str = Field(..., description='The user ID')
    chatTopicId: str = Field(..., description='The chat topic ID')
    entryId: Optional[str] = Field(None, description='The chat ID')


class ChatPromptIn(BaseModel):
    query: str = Field(..., description='The query to send')
    userId: str = Field(..., description='The user ID')
    chatTopicId: Optional[str] = Field(None, description='The chat topic ID')
    entryId: Optional[str] = Field(None, description='The chat ID')


class ChatOut(BaseModel):
    response: str = Field(..., description='The response to send')
    chatTopicId: str = Field(..., description='The chat topic ID')
    userId: str = Field(..., description='The user ID')
    entryId: str = Field(..., description='The chat ID')


class SendChatChunkIn(BaseModel):
    chatTopicId: str = Field(..., description='The chat topic ID')
    userId: str = Field(..., description='The user ID')
    entryId: str = Field(..., description='The chat ID')
    response: str = Field(..., description='The response to send')
