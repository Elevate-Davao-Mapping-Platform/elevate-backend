from models.entity import Entities
from pynamodb.attributes import UnicodeAttribute
from pydantic import BaseModel

class ChatTopic(Entities, discriminator='ChatTopic'):
    # hk: ChatTopic#<userId>
    # rk: v<version_number>#<entryId>
    
    title = UnicodeAttribute(null=False)

class ChatTopicIn(BaseModel):
    title: str
    userId: str
