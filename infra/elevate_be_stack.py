from aws_cdk import CfnOutput, Stack
from constructs import Construct

from infra.appsync.appsync import AppsyncAPI
from infra.cognito.identity_pool import IdentityPoolConstruct
from infra.cognito.user_pool import UserPoolConstruct
from infra.config import Config
from infra.dynamodb.entity_table import EntityTable
from infra.functions.rag_api import LLMRAGAPI
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

        # LLM RAG API
        entity_table = EntityTable(self, 'EntityTable', config=self.config)
        llm_rag_api = LLMRAGAPI(
            self,
            'LLMRAGAPI',
            config=self.config,
            entity_table=entity_table,
        )

        # Appsync API
        api = AppsyncAPI(
            self,
            f'{main_resources_name}-{stage}-appsync-api',
            config=self.config,
            cognito_user_pool=cognito_user_pool,
            llm_rag_api=llm_rag_api,
            entity_table=entity_table.entity_table,
        )

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

        # Outputs
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
