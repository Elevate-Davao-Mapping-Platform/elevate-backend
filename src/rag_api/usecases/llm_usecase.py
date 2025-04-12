import json
import os
from http import HTTPStatus
from typing import List, Optional

import boto3
from aws_lambda_powertools import Logger
from botocore.exceptions import ClientError
from rag_api.external.graphql_gateway import GraphQLGateway
from rag_api.models.chat import ChatPromptIn, SendChatChunkIn
from rag_api.usecases.knowledge_base_usecase import KnowledgeBaseUsecase
from shared_modules.models.schema.entity import EntitySchema
from shared_modules.repositories.entity_repository import EntityRepository


class LLMUsecase:
    def __init__(self):
        self.logger = Logger()
        self.graphql_gateway = GraphQLGateway()
        self.knowledge_base_usecase = KnowledgeBaseUsecase()
        self.entity_repository = EntityRepository()

    def build_prompt(
        self,
        prompt: str,
        chat_history_context: str,
        vector_retrieval_chunks: str,
        entities: Optional[List[EntitySchema]] = None,
    ):
        """Build the prompt for the LLM."""
        entity_data = (
            '\n'.join([entity.model_dump_json() for entity in entities]) if entities else None
        )
        base_prompt = (
            'You are a context-aware startup ecosystem assistant for Davao City. Your goal is to help startups, '
            'investors, and ecosystem enablers by providing relevant, timely, and personalized support based on '
            "the user's needs and the local startup environment.\n\n"
            f'## User Input:\n{prompt}\n\n'
            '## Chat History:\n'
            f'{chat_history_context}\n\n'
            '## Retrieved Knowledge Base Data:\n'
            f'{vector_retrieval_chunks}\n'
        )

        entity_section = (
            (
                '## All Current Startup | Enabler Data:\n'
                f'{entity_data}\n\n'
                '(This includes information from local incubators, web-scraped directories, and structured database entries '
                'on startups, investors, and mentors.)\n\n'
            )
            if entity_data
            else ''
        )

        instructions = (
            '## Instructions:\n'
            '- Your responses must reflect the current startup landscape of Davao City.\n'
            '- Incorporate specific local context (e.g., known incubators, typical funding rounds, or local startup challenges).\n'
            '- Leverage the retrieved knowledge base to offer tailored recommendations.\n'
            '- If information is not available, ask clarifying questions instead of making assumptions.\n'
            '- Keep the response concise, friendly, and helpful.\n'
            '- Never hallucinate; rely only on the provided context.\n\n'
            '## Response:\n'
        )

        return base_prompt + entity_section + instructions

    def invoke_llm(self, prompt: str):
        """Invoke the LLM with the given prompt."""
        region_name = os.getenv('BEDROCK_AWS_REGION')
        model_id = 'us.anthropic.claude-3-5-haiku-20241022-v1:0'

        try:
            client = boto3.client('bedrock-runtime', region_name=region_name)
            model_id = 'us.anthropic.claude-3-5-haiku-20241022-v1:0'
            response = client.invoke_model_with_response_stream(
                modelId=model_id,
                body=json.dumps(
                    {
                        'anthropic_version': 'bedrock-2023-05-31',
                        'max_tokens': 4096,
                        'messages': [{'role': 'user', 'content': prompt}],
                    }
                ),
            )

            event_stream = response.get('body', {})

            for event in event_stream:
                chunk = event.get('chunk')
                if chunk:
                    message = json.loads(chunk.get('bytes').decode())
                    if message['type'] == 'content_block_delta':
                        response_chunk = message['delta']['text'] or ''
                        self.logger.debug(f'Bedrock response Chunk: {response_chunk}')
                        yield response_chunk

                    elif message['type'] == 'message_stop':
                        return '\n'

        except ClientError as e:
            self.logger.exception(f'Client error invoking Bedrock model: {e}')
            return {
                'response': str(e),
                'status': HTTPStatus.INTERNAL_SERVER_ERROR,
            }

    def generate_response(self, chat_in: ChatPromptIn, chat_history_context: str):
        """
        Generate a response to a user prompt using a vector store index and a language model.

        :param ChatPromptIn chat_in: The user prompt to generate a response for.
        :param str chat_history_context: The chat history context to use for the response.
        :return dict: A dictionary containing the response and the status code.
        """
        # Configuration
        prompt = chat_in.query
        vector_retrieval_chunks = self.knowledge_base_usecase.get_knowledge_base_data(prompt)

        _, entities, _ = self.entity_repository.get_entity_list()

        prompt = self.build_prompt(prompt, chat_history_context, vector_retrieval_chunks, entities)

        response_text = ''
        for response_chunk in self.invoke_llm(prompt):
            response_text += response_chunk

            send_chat_chunk_in = SendChatChunkIn(
                chatTopicId=chat_in.chatTopicId,
                userId=chat_in.userId,
                entryId=chat_in.entryId,
                response=response_text,
            )
            self.graphql_gateway.send_chat_chunk(send_chat_chunk_in)

        return response_text
