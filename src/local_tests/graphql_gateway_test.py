# noqa
from dotenv import load_dotenv

load_dotenv()
from rag_api.external.graphql_gateway import GraphQLGateway  # noqa: E402


def main():
    input_params = {
        'chatTopicId': 'your-chat-topic-id',
        'userId': '456',
        'entryId': '789',
        'response': 'Hello, world!',
    }

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
    graphql_gateway = GraphQLGateway()
    graphql_gateway.mutation(query=query, input_params=input_params)


if __name__ == '__main__':
    main()
