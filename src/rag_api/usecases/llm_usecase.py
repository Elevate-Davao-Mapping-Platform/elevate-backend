import json
import os
import time
from http import HTTPStatus
from typing import List, Optional

import boto3
from aws_lambda_powertools import Logger
from botocore.exceptions import ClientError
from rag_api.constants.chat_constants import ChatConstants
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
        user_entity: Optional[EntitySchema] = None,
        other_entities: Optional[List[EntitySchema]] = None,
    ):
        """Build the prompt for the LLM."""
        entity_data = (
            '\n'.join([entity.model_dump_json() for entity in other_entities])
            if other_entities
            else None
        )

        base_prompt = (
            'You are a context-aware startup ecosystem assistant for Davao City. Your goal is to help startups, '
            'investors, and ecosystem enablers by providing relevant, timely, and personalized support based on '
            "the user's needs and the local startup environment.\n\n"
            '## Conversation Context:\n'
            'The following is the relevant conversation history. Use this context to maintain continuity and build upon previous interactions:\n'
            f'{chat_history_context}\n\n'
            f'## Current User Input:\n{prompt}\n\n'
            '## Retrieved Knowledge Base Data:\n'
            f'{vector_retrieval_chunks}\n'
        )

        current_entity_section = (
            ('## Current User Data:\n' f'{user_entity.model_dump_json()}\n\n')
            if user_entity
            else ''
        )

        other_entities_section = (
            (
                f'{entity_data}\n\n'
                '(This includes information from local incubators, web-scraped directories, and structured database entries '
                'on startups, investors, and mentors.)\n\n'
            )
            if entity_data
            else ''
        )

        instructions = (
            '## Instructions:\n'
            '- Maintain conversation continuity by referencing and building upon the previous chat context\n'
            '- If the current question relates to previous discussion, explicitly acknowledge and connect the points\n'
            '- Your responses must reflect the current startup landscape of Davao City\n'
            '- Incorporate specific local context (e.g., known incubators, typical funding rounds, or local startup challenges)\n'
            '- Leverage the retrieved knowledge base to offer tailored recommendations\n'
            '- If information is not available, ask clarifying questions instead of making assumptions\n'
            '- Keep the response concise, friendly, and helpful\n'
            '- Never hallucinate; rely only on the provided context\n\n'
            '## Response:\n'
        )

        return base_prompt + current_entity_section + other_entities_section + instructions

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

    def _send_chat_chunk(self, chat_in: ChatPromptIn, response_text: str):
        """Helper function to send chat chunks to the GraphQL gateway.

        Args:
            chat_in (ChatPromptIn): The input chat prompt containing metadata
            response_text (str): The response text to send
        """
        send_chat_chunk_in = SendChatChunkIn(
            chatTopicId=chat_in.chatTopicId,
            userId=chat_in.userId,
            entryId=chat_in.entryId,
            response=response_text,
        )
        self.graphql_gateway.send_chat_chunk(send_chat_chunk_in)

    def generate_response(self, chat_in: ChatPromptIn, chat_history_context: str):
        """
        Generate a response to a user prompt using a vector store index and a language model.

        :param ChatPromptIn chat_in: The user prompt to generate a response for.
        :param str chat_history_context: The chat history context to use for the response.
        :return dict: A dictionary containing the response and the status code.
        """
        # Configuration
        prompt = chat_in.query
        user_id = chat_in.userId
        vector_retrieval_chunks = self.knowledge_base_usecase.get_knowledge_base_data(prompt)

        _, entities, _ = self.entity_repository.get_entity_list()
        user_entity = None
        other_entities = []
        for entity in entities:
            if entity.startupId == user_id or entity.enablerId == user_id:
                user_entity = entity
            else:
                other_entities.append(entity)

        prompt = self.build_prompt(
            prompt, chat_history_context, vector_retrieval_chunks, user_entity, other_entities
        )

        response_text = ''
        chunk_buffer_list = []

        for response_chunk in self.invoke_llm(prompt):
            chunk_buffer_list.append(response_chunk)

            if len(chunk_buffer_list) < ChatConstants.CHUNK_BUFFER_LIMIT:
                continue

            response_text += ''.join(chunk_buffer_list)
            chunk_buffer_list = []

            self._send_chat_chunk(chat_in, response_text)

        time.sleep(1)

        if chunk_buffer_list:
            response_text += ''.join(chunk_buffer_list)
            self._send_chat_chunk(chat_in, response_text)

        time.sleep(1)

        self._send_chat_chunk(chat_in, ChatConstants.END_OF_MESSAGE)

        return response_text
