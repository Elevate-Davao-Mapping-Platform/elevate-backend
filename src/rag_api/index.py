import json
import os
from http import HTTPStatus

import boto3
from botocore.exceptions import ClientError
from constants.chat_constants import ChatType
from llama_index.core import VectorStoreIndex
from llama_index.embeddings.bedrock import BedrockEmbedding, Models
from llama_index.llms.bedrock import Bedrock
from llama_index.vector_stores.pinecone import PineconeVectorStore
from models.chat import ChatIn, ChatOut, ChatPromptIn
from models.chat_topic import ChatTopicIn
from pinecone import Pinecone
from repositories.chat_repository import ChatRepository
from repositories.chat_topic_repository import ChatTopicRepository
from utils.logger import logger


def generate_response(chat_in: ChatPromptIn, chat_history_context: str):
    # Configuration
    secret_name = 'elevate/pinecone-api-key'
    region_name = os.getenv('BEDROCK_AWS_REGION')

    # Create a Session with AWS
    session = boto3.Session(region_name=region_name)

    # Create a Secrets Manager client using the session
    secrets_client = session.client(service_name='secretsmanager')

    # Retrieve the Pinecone API key from AWS Secrets Manager
    try:
        get_secret_value_response = secrets_client.get_secret_value(SecretId=secret_name)
        secret_string = get_secret_value_response['SecretString']
        secret = json.loads(secret_string)
        api_key = secret['apiKey']
        os.environ['PINECONE_API_KEY'] = api_key

    except ClientError as e:
        logger.error(f'Error retrieving Pinecone API key: {e}')
        return {
            'response': str(e),
            'status': HTTPStatus.INTERNAL_SERVER_ERROR,
        }

    # Initialize Pinecone
    try:
        pc = Pinecone(api_key=api_key)
        pinecone_index_name = 'elevate-vector-db'
        pinecone_index = pc.Index(pinecone_index_name)
        vector_store = PineconeVectorStore(pinecone_index=pinecone_index)

        # Initialize the embedding model
        embed_model = BedrockEmbedding(
            model_name=Models.TITAN_EMBEDDING_V2_0.value,
            region_name=region_name,
        )

        # Create a vector store index
        index = VectorStoreIndex.from_vector_store(vector_store=vector_store, embed_model=embed_model)

        # Initialize the language model
        llm = Bedrock(
            model='anthropic.claude-v2:1',
            region_name=region_name,
        )

        # Create a query engine
        query_engine = index.as_query_engine(llm=llm)

        # Perform the query
        query = (
            f'You are an expert in Davao City Startups. '
            f'You are given whatever context thrown at you and you will answer the user prompt without hallucinating '
            'or mentioning youre not given enough context. '
            f'Chat History: {chat_history_context}\n\nUser Prompt: {chat_in.query}\n\nResponse:'
        )
        llm_result = query_engine.query(query)

        logger.debug(f'Response: {llm_result}')

        response = {
            'response': llm_result.response,
            'status': HTTPStatus.OK,
        }
        return response

    except Exception as e:
        logger.error(f'Error generating response: {e}')
        return {
            'response': str(e),
            'status': HTTPStatus.INTERNAL_SERVER_ERROR,
        }


def process_prompt(chat_in: ChatPromptIn):
    chat_topic_repository = ChatTopicRepository()
    chat_repository = ChatRepository()

    # Check if chat topic exists
    chat_topic_id = chat_in.chatTopicId
    status = HTTPStatus.OK
    if chat_topic_id:
        status, _, message = chat_topic_repository.query_chat_topic(chat_in.userId, chat_topic_id)

    if not chat_topic_id or status != HTTPStatus.OK:
        status, chat_topic, message = chat_topic_repository.store_chat_topic(
            chat_topic_in=ChatTopicIn(
                userId=chat_in.userId,
                title=chat_in.query,
            )
        )
        if status != HTTPStatus.OK:
            return {
                'response': message,
                'status': status,
            }

        chat_topic_id = chat_topic.entryId

    _, chats, _ = chat_repository.get_chats_in_topic(chat_topic_id, chat_in.userId)
    chats = chats or []
    chats = sorted(chats, key=lambda x: x.createDate, reverse=True)
    chat_history_for_prompt = '\n'.join([chat.message for chat in chats])

    llm_response = generate_response(chat_in, chat_history_for_prompt)

    if llm_response['status'] != HTTPStatus.OK:
        return llm_response

    # Store the query chat
    user_prompt_chat_in = ChatIn(
        userId=chat_in.userId,
        chatTopicId=chat_topic_id,
        message=chat_in.query,
        type=ChatType.USER_PROMPT.value,
    )
    status, user_prompt_chat, message = chat_repository.store_chat(
        chat_in=user_prompt_chat_in,
    )
    if status != HTTPStatus.OK:
        return {
            'response': message,
            'status': status,
        }

    # Store the response chat
    llm_response_chat_in = ChatIn(
        userId=chat_in.userId,
        chatTopicId=chat_topic_id,
        message=llm_response['response'],
        type=ChatType.LLM_RESPONSE.value,
    )
    status, _, message = chat_repository.store_chat(
        chat_in=llm_response_chat_in,
    )
    if status != HTTPStatus.OK:
        return {
            'response': message,
            'status': status,
        }

    return ChatOut(
        response=llm_response['response'],
        chatTopicId=chat_topic_id,
        userId=chat_in.userId,
        chatId=user_prompt_chat.entryId,
    ).model_dump()


def handler(event, context):
    _ = context
    logger.debug(f'Received event: {event}')

    body = event['arguments']
    chat_in = ChatPromptIn(**body['input'])
    response = process_prompt(chat_in)

    return response
