import json
import os
from http import HTTPStatus

import boto3
from aws_lambda_powertools import Logger
from botocore.exceptions import ClientError
from mypy_boto3_bedrock_agent_runtime.client import AgentsforBedrockRuntimeClient
from mypy_boto3_bedrock_agent_runtime.type_defs import RetrieveRequestTypeDef
from rag_api.models.chat import ChatPromptIn


class LLMUsecase:
    def __init__(self):
        self.logger = Logger()

    def generate_response(self, chat_in: ChatPromptIn, chat_history_context: str):
        """
        Generate a response to a user prompt using a vector store index and a language model.

        :param ChatPromptIn chat_in: The user prompt to generate a response for.
        :param str chat_history_context: The chat history context to use for the response.
        :return dict: A dictionary containing the response and the status code.
        """
        # Configuration
        prompt = chat_in.query

        region_name = os.getenv('BEDROCK_AWS_REGION')
        knowledge_base_id = os.getenv('KNOWLEDGE_BASE_ID') or 'ORGCXIYNDH'
        number_of_results = 5
        bedrock_agent_runtime_client: AgentsforBedrockRuntimeClient = boto3.client(
            'bedrock-agent-runtime', region_name=region_name
        )

        response: RetrieveRequestTypeDef = bedrock_agent_runtime_client.retrieve(
            knowledgeBaseId=knowledge_base_id,
            retrievalQuery={'text': prompt},
            retrievalConfiguration={
                'vectorSearchConfiguration': {'numberOfResults': number_of_results}
            },
        )

        text_results = []
        retrieval_results = response.get('retrievalResults')
        for result in retrieval_results:
            content = result.get('content')
            text = content.get('text')
            text_results.append(text)

        search_with_text = '\n'.join(text_results)

        try:
            self.logger.debug(f'Search with text: {search_with_text}')

            # Format system prompts
            prompt = (
                'You are a context-aware startup ecosystem assistant for Davao City. Your goal is to help startups, '
                'investors, and ecosystem enablers by providing relevant, timely, and personalized support based on '
                "the user's needs and the local startup environment.\n\n"
                f'## User Input:\n{prompt}\n\n'
                '## Chat History:\n'
                f'{chat_history_context}\n\n'
                '## Retrieved Knowledge Base Data:\n'
                f'{search_with_text}\n'
                '(This includes information from local incubators, web-scraped directories, and structured database entries '
                'on startups, investors, and mentors.)\n\n'
                '## Instructions:\n'
                '- Your responses must reflect the current startup landscape of Davao City.\n'
                '- Incorporate specific local context (e.g., known incubators, typical funding rounds, or local startup challenges).\n'
                '- Leverage the retrieved knowledge base to offer tailored recommendations.\n'
                '- If information is not available, ask clarifying questions instead of making assumptions.\n'
                '- Keep the response concise, friendly, and helpful.\n'
                '- Never hallucinate; rely only on the provided context.\n\n'
                '## Response:\n'
            )

            try:
                client = boto3.client('bedrock-runtime', region_name=region_name)
                model_id = 'us.anthropic.claude-3-5-haiku-20241022-v1:0'
                response = client.invoke_model(
                    modelId=model_id,
                    body=json.dumps(
                        {
                            'anthropic_version': 'bedrock-2023-05-31',
                            'max_tokens': 1000,
                            'messages': [{'role': 'user', 'content': prompt}],
                        }
                    ),
                    contentType='application/json',
                    accept='application/json',
                )

                # Extract the response text
                response_body = json.loads(response['body'].read())
                self.logger.debug(f'Bedrock response: {response_body}')
                llm_response = response_body.get('content', 'No response content')
                response_text = llm_response[0]['text']

                response = {
                    'response': response_text,
                    'status': HTTPStatus.OK,
                }
                return response

            except ClientError as e:
                self.logger.exception(f'Error invoking Bedrock model: {e}')
                return {
                    'response': str(e),
                    'status': HTTPStatus.INTERNAL_SERVER_ERROR,
                }

        except Exception as e:
            self.logger.exception(f'Error generating response: {e}')
            return {
                'response': str(e),
                'status': HTTPStatus.INTERNAL_SERVER_ERROR,
            }
