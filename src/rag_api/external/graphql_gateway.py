import os
from typing import Optional

from aws_lambda_powertools import Logger
from gql import Client, gql
from gql.transport.aiohttp import AIOHTTPTransport
from rag_api.models.chat import SendChatChunkIn


class GraphQLGateway:
    def __init__(self):
        self.url = os.getenv('GRAPHQL_URL')
        self.api_key = os.getenv('API_KEY')
        headers = {
            'Accept': '*/*',
            'Content-Type': 'application/json',
            'x-api-key': self.api_key,
        }
        self.transport = AIOHTTPTransport(url=self.url, headers=headers)
        self.client = Client(transport=self.transport, fetch_schema_from_transport=False)
        self.logger = Logger()

    def mutation(self, query: str, input_params: Optional[dict] = None):
        """Send a mutation to the GraphQL gateway.

        :param str query: The GraphQL mutation query.
        :param dict input_params: The input parameters for the mutation.
        :return dict: The response from the GraphQL gateway.
        """
        try:
            response = self.client.execute(gql(query), variable_values=input_params)
            return response

        except Exception as e:
            self.logger.exception(f'Error sending mutation to GraphQL gateway: {e}')
            raise e

    def send_chat_chunk(self, send_chat_chunk_in: SendChatChunkIn):
        """
        Send a chat chunk to the GraphQL gateway.

        :param SendChatChunkIn send_chat_chunk_in: The chat chunk to send.
        :return dict: The response from the GraphQL gateway.
        """
        query = """
            mutation SendChatChunk($chatTopicId: String!, $userId: String!, $entryId: String!, $response: String!) {
                sendChatChunk(
                    input: {
                        chatTopicId: $chatTopicId
                        userId: $userId
                        entryId: $entryId
                        response: $response
                    }
                ) {
                    entryId
                    userId
                    chatTopicId
                    response
                }
            }
        """
        return self.mutation(
            query=query,
            input_params=send_chat_chunk_in.model_dump(),
        )
