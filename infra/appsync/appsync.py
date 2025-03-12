from os import path
from typing import Optional

from aws_cdk import aws_appsync as appsync
from aws_cdk import aws_cognito as cognito
from aws_cdk import aws_dynamodb as dynamodb
from constructs import Construct

from infra.config import Config


class AppsyncAPI(Construct):
    """Constructs an AppSync GraphQL API with Lambda and DynamoDB data sources."""

    def __init__(self, scope: Construct, construct_id: str, config: Config, **kwargs) -> None:
        cognito_user_pool: cognito.UserPool = kwargs.pop('cognito_user_pool', None)
        llm_rag_api = kwargs.pop('llm_rag_api', None)
        entity_table: dynamodb.Table = kwargs.pop('entity_table', None)

        super().__init__(scope, construct_id, **kwargs)

        self.graphql_url: str
        self.api_key: Optional[str]
        self.api_id: str

        self.config = config
        self.api = self._create_api(cognito_user_pool)

        # Set up data sources and resolvers
        self._setup_llm_resolvers(llm_rag_api)
        self._setup_chat_resolvers(entity_table)

        # Store API outputs
        self.graphql_url = self.api.graphql_url
        self.api_key = self.api.api_key
        self.api_id = self.api.api_id

    def _create_api(self, cognito_user_pool: cognito.UserPool) -> appsync.GraphqlApi:
        """Creates and configures the GraphQL API."""
        graphql_api_name = f'{self.config.main_resources_name}-{self.config.stage}-graphql-service'
        gql_schema = path.join(path.dirname(__file__), '..', '..', 'schema', 'schema.graphql')

        return appsync.GraphqlApi(
            self,
            'Api',
            name=graphql_api_name,
            definition=appsync.Definition.from_file(gql_schema),
            authorization_config=appsync.AuthorizationConfig(
                default_authorization=appsync.AuthorizationMode(
                    authorization_type=appsync.AuthorizationType.API_KEY
                ),
                additional_authorization_modes=[
                    appsync.AuthorizationMode(
                        authorization_type=appsync.AuthorizationType.USER_POOL,
                        user_pool_config=appsync.UserPoolConfig(
                            user_pool=cognito_user_pool,
                        ),
                    ),
                ],
            ),
            xray_enabled=True,
        )

    def _setup_llm_resolvers(self, llm_rag_api) -> None:
        """Sets up Lambda data source and resolvers for LLM functionality."""
        llm_service_ds = self.api.add_lambda_data_source(
            f'{self.config.main_resources_name}-{self.config.stage}-llm-service-data-source',
            llm_rag_api.lambda_rag_api,
        )

        llm_service_ds.create_resolver(
            f'{self.config.main_resources_name}-{self.config.stage}-MutationQueryChat',
            type_name='Mutation',
            field_name='queryChat',
            request_mapping_template=appsync.MappingTemplate.lambda_request(),
            response_mapping_template=appsync.MappingTemplate.lambda_result(),
        )

    def _setup_chat_resolvers(self, entity_table: dynamodb.Table) -> None:
        """Sets up DynamoDB data source and resolvers for chat functionality."""
        chat_ds = self.api.add_dynamo_db_data_source(
            f'{self.config.main_resources_name}-{self.config.stage}-ChatDDBsource', entity_table
        )

        # Resolver for getChatTopics
        chat_ds.create_resolver(
            f'{self.config.main_resources_name}-{self.config.stage}-QueryGetChatTopicsResolver',
            type_name='Query',
            field_name='getChatTopics',
            request_mapping_template=appsync.MappingTemplate.from_string(
                """
                {
                    "version": "2017-02-28",
                    "operation": "Query",
                    "query": {
                        "expression": "hashKey = :hashKey",
                        "expressionValues": {
                            ":hashKey": $util.dynamodb.toDynamoDBJson("ChatTopic#$context.arguments.userId")
                        }
                    }
                }
                """
            ),
            response_mapping_template=appsync.MappingTemplate.dynamo_db_result_list(),
        )

        # Resolver for getChats
        chat_ds.create_resolver(
            f'{self.config.main_resources_name}-{self.config.stage}-QueryGetChatsResolver',
            type_name='Query',
            field_name='getChats',
            request_mapping_template=appsync.MappingTemplate.from_string(
                """
                {
                    "version": "2017-02-28",
                    "operation": "Query",
                    "query": {
                        "expression": "hashKey = :hashKey and begins_with(rangeKey, :rangeKeyPrefix)",
                        "expressionValues": {
                            ":hashKey": $util.dynamodb.toDynamoDBJson("Chat#$context.arguments.userId"),
                            ":rangeKeyPrefix": $util.dynamodb.toDynamoDBJson("v0#$context.arguments.chatTopicId#")
                        }
                    }
                }
                """
            ),
            response_mapping_template=appsync.MappingTemplate.dynamo_db_result_list(),
        )
