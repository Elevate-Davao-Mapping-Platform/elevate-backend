from enum import Enum


class ChatType(str, Enum):
    USER_PROMPT = 'USER_PROMPT'
    LLM_RESPONSE = 'LLM_RESPONSE'


class ChatConstants:
    CHUNK_BUFFER_LIMIT = 10
    END_OF_MESSAGE = 'END_OF_MESSAGE'
