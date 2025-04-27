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
        get_analytics_lambda: lambda_.Function = kwargs.pop('get_analytics_lambda', None)
        get_saved_profiles_lambda: lambda_.Function = kwargs.pop('get_saved_profiles_lambda', None)
        suggestions_cron_lambda: lambda_.Function = kwargs.pop('suggestions_cron_lambda', None)

        super().__init__(scope, construct_id, **kwargs)

        self.config = config
        self.api = self._create_api(cognito_user_pool, entity_table)

        # Set up data sources and resolvers
        entity_table_data_source = self._setup_entity_table_data_source(entity_table)

        # Create a Lambda data source for the suggestions cron
        suggestions_cron_ds = self.api.add_lambda_data_source(
            f'{self.config.prefix}-suggestions-cron-data-source',
            suggestions_cron_lambda,
        )

        self._setup_llm_resolvers(llm_rag_api)
        self._setup_chat_resolvers(entity_table_data_source)
        self._setup_startup_resolvers(entity_table_data_source, suggestions_cron_ds)
        self._setup_enabler_resolvers(entity_table_data_source, suggestions_cron_ds)
        self._setup_entity_list_resolvers(entity_table_data_source)
        self._setup_suggestion_resolvers(get_suggestions_lambda)
        self._setup_profile_resolvers(entity_table_data_source, get_saved_profiles_lambda)
        self._setup_analytics_resolvers(get_analytics_lambda)
        self._setup_admin_resolvers(entity_table_data_source)

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
                        name=f'{self.config.prefix}-appsync-key',
                        description='Used for the Elevate API. Do not share this key with anyone. Do not delete this key.',
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
        self,
        entity_table_data_source: appsync.DynamoDbDataSource,
        suggestions_cron_ds: appsync.LambdaDataSource,
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

        # Create the functions that will be part of the pipeline
        update_startup_js = f'{folder_root}/updateStartup.js'
        update_startup_function = appsync.AppsyncFunction(
            self,
            f'{self.config.prefix}-UpdateStartupFunction',
            name=f'{self.config.prefix_no_symbols}UpdateStartupFunction',
            api=self.api,
            data_source=entity_table_data_source,
            code=appsync.Code.from_asset(update_startup_js),
            runtime=appsync.FunctionRuntime.JS_1_0_0,
        )

        trigger_suggestions_function = appsync.AppsyncFunction(
            self,
            f'{self.config.prefix}-TriggerSuggestionsFunction',
            name=f'{self.config.prefix_no_symbols}TriggerSuggestionsFunction',
            api=self.api,
            data_source=suggestions_cron_ds,
            code=appsync.Code.from_inline(
                """
                export function request(ctx) {
                    return {
                        operation: "Invoke",
                        invocationType: "Event",
                        payload: ctx,
                    };
                }

                export function response(ctx) {
                    return ctx.prev.result;
                }
                """
            ),
            runtime=appsync.FunctionRuntime.JS_1_0_0,
        )

        # Create the pipeline resolver
        self.api.create_resolver(
            f'{self.config.prefix}-MutationUpdateStartupResolver',
            type_name='Mutation',
            field_name='updateStartup',
            code=appsync.Code.from_inline(
                """
                export function request(ctx) {
                    return ctx.args;
                }

                export function response(ctx) {
                    return ctx.prev.result;
                }
            """
            ),
            runtime=appsync.FunctionRuntime.JS_1_0_0,
            pipeline_config=[update_startup_function, trigger_suggestions_function],
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
        self,
        entity_table_data_source: appsync.DynamoDbDataSource,
        suggestions_cron_ds: appsync.LambdaDataSource,
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

        # Create the functions that will be part of the pipeline
        update_enabler_js = f'{folder_root}/updateEnabler.js'
        update_enabler_function = appsync.AppsyncFunction(
            self,
            f'{self.config.prefix}-UpdateEnablerFunction',
            name=f'{self.config.prefix_no_symbols}UpdateEnablerFunction',
            api=self.api,
            data_source=entity_table_data_source,
            code=appsync.Code.from_asset(update_enabler_js),
            runtime=appsync.FunctionRuntime.JS_1_0_0,
        )

        trigger_suggestions_function = appsync.AppsyncFunction(
            self,
            f'{self.config.prefix}-TriggerEnablerSuggestionsFunction',
            name=f'{self.config.prefix_no_symbols}TriggerEnablerSuggestionsFunction',
            api=self.api,
            data_source=suggestions_cron_ds,
            code=appsync.Code.from_inline(
                """
                export function request(ctx) {
                    return {
                        operation: "Invoke",
                        invocationType: "Event",
                        payload: ctx,
                    };
                }

                export function response(ctx) {
                    return ctx.prev.result;
                }
                """
            ),
            runtime=appsync.FunctionRuntime.JS_1_0_0,
        )

        # Create the pipeline resolver
        self.api.create_resolver(
            f'{self.config.prefix}-MutationUpdateEnablerResolver',
            type_name='Mutation',
            field_name='updateEnabler',
            code=appsync.Code.from_inline(
                """
                export function request(ctx) {
                    return ctx.args;
                }

                export function response(ctx) {
                    return ctx.prev.result;
                }
                """
            ),
            runtime=appsync.FunctionRuntime.JS_1_0_0,
            pipeline_config=[update_enabler_function, trigger_suggestions_function],
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

    def _setup_suggestion_resolvers(
        self,
        get_suggestions_lambda: lambda_.Function,
    ) -> None:
        """Sets up DynamoDB data source and resolvers for suggestion functionality."""
        suggestion_lambda_data_source = self.api.add_lambda_data_source(
            f'{self.config.prefix}-suggestion-data-source',
            get_suggestions_lambda,
        )

        suggestion_lambda_data_source.create_resolver(
            f'{self.config.prefix}-QueryGetSuggestionsResolver',
            type_name='Query',
            field_name='getSuggestions',
        )

    def _setup_profile_resolvers(
        self,
        entity_table_data_source: appsync.DynamoDbDataSource,
        get_saved_profiles_lambda: lambda_.Function,
    ) -> None:
        """Sets up DynamoDB data source and resolvers for profile functionality."""
        folder_root = './infra/appsync/appsync_js/profiles'

        save_profile_js = f'{folder_root}/saveProfile.js'
        entity_table_data_source.create_resolver(
            f'{self.config.prefix}-MutationSaveProfileResolver',
            type_name='Mutation',
            field_name='saveProfile',
            code=appsync.Code.from_asset(save_profile_js),
            runtime=appsync.FunctionRuntime.JS_1_0_0,
        )

        unsave_profile_js = f'{folder_root}/unsaveProfile.js'
        entity_table_data_source.create_resolver(
            f'{self.config.prefix}-MutationUnsaveProfileResolver',
            type_name='Mutation',
            field_name='unsaveProfile',
            code=appsync.Code.from_asset(unsave_profile_js),
            runtime=appsync.FunctionRuntime.JS_1_0_0,
        )

        get_saved_profiles_lambda_resolver = self.api.add_lambda_data_source(
            f'{self.config.prefix}-get-saved-profiles-lambda-data-source',
            get_saved_profiles_lambda,
        )
        get_saved_profiles_lambda_resolver.create_resolver(
            f'{self.config.prefix}-QueryGetSavedProfilesResolver',
            type_name='Query',
            field_name='getSavedProfiles',
        )

    def _setup_analytics_resolvers(self, analytics_lambda: lambda_.Function) -> None:
        """Sets up DynamoDB data source and resolvers for analytics functionality."""
        analytics_data_source = self.api.add_lambda_data_source(
            f'{self.config.prefix}-analytics-data-source',
            analytics_lambda,
        )

        analytics_data_source.create_resolver(
            f'{self.config.prefix}-QueryGetAnalyticsResolver',
            type_name='Query',
            field_name='getAnalytics',
        )

    def _setup_admin_resolvers(self, entity_table_data_source: appsync.DynamoDbDataSource) -> None:
        """Sets up DynamoDB data source and resolvers for entity list functionality."""
        folder_root = './infra/appsync/appsync_js/admin'

        request_name_change_js = f'{folder_root}/requestNameChange.js'
        entity_table_data_source.create_resolver(
            f'{self.config.prefix}-MutationRequestNameChange',
            type_name='Mutation',
            field_name='requestNameChange',
            code=appsync.Code.from_asset(request_name_change_js),
            runtime=appsync.FunctionRuntime.JS_1_0_0,
        )

        get_name_change_requests_js = f'{folder_root}/getNameChangeRequests.js'
        entity_table_data_source.create_resolver(
            f'{self.config.prefix}-QueryGetNameChangeRequests',
            type_name='Query',
            field_name='getNameChangeRequests',
            code=appsync.Code.from_asset(get_name_change_requests_js),
            runtime=appsync.FunctionRuntime.JS_1_0_0,
        )

        # # Create the pipeline resolver functions
        get_name_change_request_js = f'{folder_root}/getNameChangeRequest.js'
        update_name_change_request_and_entity_js = f'{folder_root}/updateNameChangeAndEntity.js'
        
        # Create the resolver functions
        get_name_change_request_fn = appsync.AppsyncFunction(
            self,
            f'{self.config.prefix}-GetNameChangeRequestFunction',
            code=appsync.Code.from_asset(get_name_change_request_js),
            runtime=appsync.FunctionRuntime.JS_1_0_0,
            name=f'{self.config.prefix_no_symbols}GetNameChangeRequest',
            data_source=entity_table_data_source,
            api=self.api,
        )
        
        update_name_change_request_and_entity_fn = appsync.AppsyncFunction(
            self,
            f'{self.config.prefix}-UpdateNameChangeRequestAndEntityFunction',
            code=appsync.Code.from_asset(update_name_change_request_and_entity_js),
            runtime=appsync.FunctionRuntime.JS_1_0_0,
            name=f'{self.config.prefix_no_symbols}UpdateNameChangeRequestAndEntity',
            data_source=entity_table_data_source,
            api=self.api,
        )
        
        respond_name_change_js = f'{folder_root}/respondNameChange.js'
        self.api.create_resolver(
            f'{self.config.prefix}-MutationRespondNameChange',
            type_name='Mutation',
            field_name='respondNameChange',
            code=appsync.Code.from_asset(respond_name_change_js),
            runtime=appsync.FunctionRuntime.JS_1_0_0,
            pipeline_config=[get_name_change_request_fn, update_name_change_request_and_entity_fn],
        )