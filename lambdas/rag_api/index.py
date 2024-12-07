import json
import os
from http import HTTPStatus

import boto3
from botocore.exceptions import ClientError
from llama_index.core import VectorStoreIndex
from llama_index.embeddings.bedrock import BedrockEmbedding, Models
from llama_index.llms.bedrock import Bedrock
from llama_index.vector_stores.pinecone import PineconeVectorStore
from pinecone import Pinecone
from utils.logger import logger


def prompt(input_text: str):
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
        result = query_engine.query(input_text)
        logger.debug(f'Response: {result}')
        response = {
            'response': result.response,
            'status': HTTPStatus.OK,
        }
        return response

    except Exception as e:
        logger.error(f'Error generating response: {e}')
        return {
            'response': str(e),
            'status': HTTPStatus.INTERNAL_SERVER_ERROR,
        }


def handler(event, context):
    _ = context
    logger.debug(f'Received event: {event}')

    body = event['arguments']
    prompt_text = body['input']['query']
    response = prompt(prompt_text)
    return response
