from aws_cdk import CfnOutput, Stack
from constructs import Construct

from infra.appsync.appsync import AppsyncAPI
from infra.cognito.identity_pool import IdentityPoolConstruct
from infra.cognito.user_pool import UserPoolConstruct
from infra.config import Config
from infra.dynamodb.entity_table import EntityTable
from infra.functions.email_sender import EmailSender
from infra.functions.get_analytics import GetAnalytics
from infra.functions.get_saved_profiles import GetSavedProfiles
from infra.functions.get_suggestions import GetSuggestions
from infra.functions.rag_api import LLMRAGAPI
from infra.functions.suggestions_cron import SuggestionsCron
from infra.layers.layers import CommonDependenciesLayer
from infra.s3.general_bucket import GeneralBucketConstruct


class ElevateBeStack(Stack):
    def __init__(
        self, scope: Construct, construct_id: str, main_resources_name: str, stage: str, **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Initialize configuration
        self.config = Config(
            scope=scope,
            stage=stage,
            main_resources_name=main_resources_name,
            account_id=self.account,
            env=kwargs.get('env'),
        )

        # Add stack tags
        for key, value in self.config.get_tags().items():
            self.tags.set_tag(key, value)

        # Create your resources here using the stage-specific configuration
        self.create_resources()

    def create_resources(self):
        main_resources_name = self.config.main_resources_name
        stage = self.config.stage

        # Create Cognito User Pool using the new construct
        cognito_construct = UserPoolConstruct(self, 'CognitoConstruct', config=self.config)
        cognito_user_pool = cognito_construct.user_pool
        cognito_user_pool_client = cognito_construct.user_pool_client

        entity_table = EntityTable(self, 'EntityTable', config=self.config)

        # ---------------------------------------------------------------------------- #
        #                               Lambda Functions                               #
        # ---------------------------------------------------------------------------- #
        common_dependencies_layer = CommonDependenciesLayer(
            self,
            'CommonDependenciesLayer',
            config=self.config,
        )
        common_dependencies_layer = common_dependencies_layer.get_layer()

        llm_rag_api = LLMRAGAPI(
            self,
            'LLMRAGAPI',
            config=self.config,
            entity_table=entity_table,
            common_dependencies_layer=common_dependencies_layer,
        )

        email_sender = EmailSender(
            self,
            'EmailSender',
            config=self.config,
            common_dependencies_layer=common_dependencies_layer,
        )

        get_suggestions = GetSuggestions(
            self,
            'GetSuggestions',
            config=self.config,
            entity_table=entity_table,
            common_dependencies_layer=common_dependencies_layer,
        )

        get_analytics = GetAnalytics(
            self,
            'GetAnalytics',
            config=self.config,
            entity_table=entity_table,
            common_dependencies_layer=common_dependencies_layer,
        )

        get_saved_profiles = GetSavedProfiles(
            self,
            'GetSavedProfiles',
            config=self.config,
            entity_table=entity_table,
            common_dependencies_layer=common_dependencies_layer,
        )

        # Suggestions Cron Job
        suggestions_cron_lambda = SuggestionsCron(
            self,
            'SuggestionsCron',
            config=self.config,
            entity_table=entity_table,
            common_dependencies_layer=common_dependencies_layer,
        )

        # ---------------------------------------------------------------------------- #
        #                                Appsync Config                                #
        # ---------------------------------------------------------------------------- #
        api = AppsyncAPI(
            self,
            f'{main_resources_name}-{stage}-appsync-api',
            config=self.config,
            cognito_user_pool=cognito_user_pool,
            llm_rag_api=llm_rag_api,
            entity_table=entity_table.entity_table,
            get_suggestions_lambda=get_suggestions.get_suggestions_lambda,
            get_analytics_lambda=get_analytics.get_analytics_lambda,
            get_saved_profiles_lambda=get_saved_profiles.get_saved_profiles_lambda,
            suggestions_cron_lambda=suggestions_cron_lambda.lambda_suggestions_cron,
            email_queue=email_sender.email_queue,
        )

        llm_rag_api.set_appsync_api(api)

        # Create S3 bucket using the new construct
        general_bucket_construct = GeneralBucketConstruct(
            self, 'GeneralBucketConstruct', config=self.config
        )
        general_bucket = general_bucket_construct.bucket

        # Create Identity Pool using the new construct
        identity_pool_construct = IdentityPoolConstruct(
            self,
            'IdentityPoolConstruct',
            config=self.config,
            user_pool_client=cognito_user_pool_client,
            user_pool_provider_name=cognito_user_pool.user_pool_provider_name,
        )
        cognito_authenticated_role = identity_pool_construct.authenticated_role

        # Add Cognito access to the bucket
        general_bucket_construct.add_cognito_access(cognito_authenticated_role)

        # ---------------------------------------------------------------------------- #
        #                                    Outputs                                   #
        # ---------------------------------------------------------------------------- #
        CfnOutput(self, 'GraphQLAPIID', value=api.api_id)
        CfnOutput(self, 'GraphQLAPIURL', value=api.graphql_url)
        CfnOutput(self, 'GraphQL API Key', value=api.api_key)
        CfnOutput(
            self,
            'UserPoolId',
            value=cognito_user_pool.user_pool_id,
            export_name=f'UserPoolId-{stage}',
        )
        CfnOutput(
            self,
            'AppClientId',
            value=cognito_user_pool_client.user_pool_client_id,
            export_name=f'AppClientId-{stage}',
        )
        CfnOutput(
            self,
            'GeneralBucketName',
            value=general_bucket.bucket_name,
        )
        CfnOutput(
            self,
            'IdentityPoolId',
            value=identity_pool_construct.identity_pool.attr_id,
        )
