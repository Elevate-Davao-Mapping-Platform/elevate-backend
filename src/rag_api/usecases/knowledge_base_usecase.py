import os

import boto3
from aws_lambda_powertools import Logger
from mypy_boto3_bedrock_agent_runtime.client import AgentsforBedrockRuntimeClient
from mypy_boto3_bedrock_agent_runtime.type_defs import RetrieveRequestTypeDef


class KnowledgeBaseUsecase:
    def __init__(self):
        self.logger = Logger()
        self.region_name = os.getenv('BEDROCK_AWS_REGION')
        self.bedrock_agent_runtime_client: AgentsforBedrockRuntimeClient = boto3.client(
            'bedrock-agent-runtime', region_name=self.region_name
        )

    def get_knowledge_base_data(self, prompt: str, number_of_results=5):
        """Get the knowledge base data from the Bedrock Agent Runtime."""

        self.logger.info(f'Getting knowledge base data for prompt: {prompt}')

        knowledge_base_id = os.getenv('KNOWLEDGE_BASE_ID') or 'ORGCXIYNDH'

        response: RetrieveRequestTypeDef = self.bedrock_agent_runtime_client.retrieve(
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

        self.logger.info(f'Knowledge base data: {search_with_text}')
        return search_with_text
