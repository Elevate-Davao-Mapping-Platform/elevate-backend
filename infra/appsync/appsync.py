from os import path

import aws_cdk.aws_logs as logs
from aws_cdk import Duration, Expiration
from aws_cdk import aws_appsync as appsync
from aws_cdk import aws_cognito as cognito
from aws_cdk import aws_dynamodb as dynamodb
from aws_cdk import aws_lambda as lambda_
from constructs import Construct

from infra.config import Config


class AppsyncAPI(Construct):
    """Constructs an AppSync GraphQL API with Lambda and DynamoDB data sources."""

    def __init__(self, scope: Construct, construct_id: str, config: Config, **kwargs) -> None:
        cognito_user_pool: cognito.UserPool = kwargs.pop('cognito_user_pool', None)
        llm_rag_api = kwargs.pop('llm_rag_api', None)
        entity_table: dynamodb.Table = kwargs.pop('entity_table', None)
        get_suggestions_lambda: lambda_.Function = kwargs.pop('get_suggestions_lambda', None)

        super().__init__(scope, construct_id, **kwargs)

        self.config = config
        self.api = self._create_api(cognito_user_pool, entity_table)

        # Set up data sources and resolvers
        entity_table_data_source = self._setup_entity_table_data_source(entity_table)
        self._setup_llm_resolvers(llm_rag_api)
        self._setup_chat_resolvers(entity_table_data_source)
        self._setup_startup_resolvers(entity_table_data_source)
        self._setup_enabler_resolvers(entity_table_data_source)
        self._setup_entity_list_resolvers(entity_table_data_source)
        self._setup_suggestion_resolvers(get_suggestions_lambda)

        # Store API outputs
        self.graphql_url = self.api.graphql_url
        self.api_key = self.api.api_key
        self.api_id = self.api.api_id
        self.arn = self.api.arn

    def _create_api(
        self, cognito_user_pool: cognito.UserPool, entity_table: dynamodb.Table
    ) -> appsync.GraphqlApi:
        """Creates and configures the GraphQL API."""
        graphql_api_name = f'{self.config.prefix}-graphql-service'
        gql_schema = path.join(path.dirname(__file__), '..', '..', 'schema', 'schema.graphql')

        return appsync.GraphqlApi(
            self,
            'Api',
            name=graphql_api_name,
            definition=appsync.Definition.from_file(gql_schema),
            authorization_config=appsync.AuthorizationConfig(
                default_authorization=appsync.AuthorizationMode(
                    authorization_type=appsync.AuthorizationType.API_KEY,
                    api_key_config=appsync.ApiKeyConfig(
                        expires=Expiration.after(Duration.days(365)),
                        name=f'{self.config.prefix}-appsync-api-key',
                    ),
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
            xray_enabled=False,
            log_config=appsync.LogConfig(
                exclude_verbose_content=False,
                field_log_level=appsync.FieldLogLevel.ALL,
                retention=logs.RetentionDays.ONE_WEEK,
            ),
            environment_variables={
                'TABLE_NAME': entity_table.table_name,
            },
        )

    def _setup_entity_table_data_source(
        self, entity_table: dynamodb.Table
    ) -> appsync.DynamoDbDataSource:
        """Sets up DynamoDB data source for entity table."""
        return self.api.add_dynamo_db_data_source(
            f'{self.config.prefix}-EntityDDBsource',
            entity_table,
        )

    def _setup_llm_resolvers(self, llm_rag_api) -> None:
        """Sets up Lambda data source and resolvers for LLM functionality."""
        llm_service_ds = self.api.add_lambda_data_source(
            f'{self.config.prefix}-llm-service-data-source',
            llm_rag_api.lambda_rag_api,
        )

        folder_root = './infra/appsync/appsync_js/llm'

        send_chat_js = f'{folder_root}/sendChat.js'
        llm_service_ds.create_resolver(
            f'{self.config.prefix}-MutationQueryChat',
            type_name='Mutation',
            field_name='sendChat',
            code=appsync.Code.from_asset(send_chat_js),
            runtime=appsync.FunctionRuntime.JS_1_0_0,
        )

        send_chat_chunk_js = f'{folder_root}/sendChatChunk.js'
        non_entity_table_data_source = self.api.add_none_data_source(
            f'{self.config.prefix}-non-entity-table-data-source',
        )
        non_entity_table_data_source.create_resolver(
            f'{self.config.prefix}-MutationQueryChatChunk',
            type_name='Mutation',
            field_name='sendChatChunk',
            code=appsync.Code.from_asset(send_chat_chunk_js),
            runtime=appsync.FunctionRuntime.JS_1_0_0,
        )

    def _setup_chat_resolvers(self, entity_table_data_source: appsync.DynamoDbDataSource) -> None:
        """Sets up DynamoDB data source and resolvers for chat functionality."""
        folder_root = './infra/appsync/appsync_js/chats'

        # Resolver for getChatTopics
        get_chat_topics_js = f'{folder_root}/getChatTopics.js'
        entity_table_data_source.create_resolver(
            f'{self.config.prefix}-QueryGetChatTopicsResolver',
            type_name='Query',
            field_name='getChatTopics',
            code=appsync.Code.from_asset(get_chat_topics_js),
            runtime=appsync.FunctionRuntime.JS_1_0_0,
        )

        # Resolver for getChats
        get_chats_js = f'{folder_root}/getChats.js'
        entity_table_data_source.create_resolver(
            f'{self.config.prefix}-QueryGetChatsResolver',
            type_name='Query',
            field_name='getChats',
            code=appsync.Code.from_asset(get_chats_js),
            runtime=appsync.FunctionRuntime.JS_1_0_0,
        )

    def _setup_startup_resolvers(
        self, entity_table_data_source: appsync.DynamoDbDataSource
    ) -> None:
        """Sets up DynamoDB data source and resolvers for startup functionality."""
        folder_root = './infra/appsync/appsync_js/startups'

        create_startup_js = f'{folder_root}/createStartup.js'
        entity_table_data_source.create_resolver(
            f'{self.config.prefix}-MutationCreateStartupResolver',
            type_name='Mutation',
            field_name='createStartup',
            code=appsync.Code.from_asset(create_startup_js),
            runtime=appsync.FunctionRuntime.JS_1_0_0,
        )

        update_startup_js = f'{folder_root}/updateStartup.js'
        entity_table_data_source.create_resolver(
            f'{self.config.prefix}-MutationUpdateStartupResolver',
            type_name='Mutation',
            field_name='updateStartup',
            code=appsync.Code.from_asset(update_startup_js),
            runtime=appsync.FunctionRuntime.JS_1_0_0,
        )

        query_startup_js = f'{folder_root}/getStartupProfile.js'
        entity_table_data_source.create_resolver(
            f'{self.config.prefix}-QueryGetStartupResolver',
            type_name='Query',
            field_name='getStartupProfile',
            code=appsync.Code.from_asset(query_startup_js),
            runtime=appsync.FunctionRuntime.JS_1_0_0,
        )

    def _setup_enabler_resolvers(
        self, entity_table_data_source: appsync.DynamoDbDataSource
    ) -> None:
        """Sets up DynamoDB data source and resolvers for enabler functionality."""
        folder_root = './infra/appsync/appsync_js/enablers'

        create_enabler_js = f'{folder_root}/createEnabler.js'
        entity_table_data_source.create_resolver(
            f'{self.config.prefix}-MutationCreateEnablerResolver',
            type_name='Mutation',
            field_name='createEnabler',
            code=appsync.Code.from_asset(create_enabler_js),
            runtime=appsync.FunctionRuntime.JS_1_0_0,
        )

        update_enabler_js = f'{folder_root}/updateEnabler.js'
        entity_table_data_source.create_resolver(
            f'{self.config.prefix}-MutationUpdateEnablerResolver',
            type_name='Mutation',
            field_name='updateEnabler',
            code=appsync.Code.from_asset(update_enabler_js),
            runtime=appsync.FunctionRuntime.JS_1_0_0,
        )

        query_enabler_js = f'{folder_root}/getEnablerProfile.js'
        entity_table_data_source.create_resolver(
            f'{self.config.prefix}-QueryGetEnablerResolver',
            type_name='Query',
            field_name='getEnablerProfile',
            code=appsync.Code.from_asset(query_enabler_js),
            runtime=appsync.FunctionRuntime.JS_1_0_0,
        )

    def _setup_entity_list_resolvers(
        self, entity_table_data_source: appsync.DynamoDbDataSource
    ) -> None:
        """Sets up DynamoDB data source and resolvers for entity list functionality."""
        folder_root = './infra/appsync/appsync_js/entities'

        query_entity_list_js = f'{folder_root}/getMapList.js'
        entity_table_data_source.create_resolver(
            f'{self.config.prefix}-QueryGetEntityListResolver',
            type_name='Query',
            field_name='getMapList',
            code=appsync.Code.from_asset(query_entity_list_js),
            runtime=appsync.FunctionRuntime.JS_1_0_0,
        )

    def _setup_suggestion_resolvers(self, get_suggestions_lambda: lambda_.Function) -> None:
        """Sets up DynamoDB data source and resolvers for suggestion functionality."""
        suggestion_data_source = self.api.add_lambda_data_source(
            f'{self.config.prefix}-suggestion-data-source',
            get_suggestions_lambda,
        )

        suggestion_data_source.create_resolver(
            f'{self.config.prefix}-QueryGetSuggestionsResolver',
            type_name='Query',
            field_name='getSuggestions',
        )
