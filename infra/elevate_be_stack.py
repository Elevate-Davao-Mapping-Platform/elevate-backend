import os

from aws_cdk import CfnOutput, Duration, RemovalPolicy, Stack
from aws_cdk import aws_cognito as cognito
from aws_cdk import aws_dynamodb as dynamodb
from aws_cdk import aws_iam as iam
from aws_cdk import aws_s3 as s3
from constructs import Construct

from infra.appsync import AppsyncAPI
from infra.entity_table import EntityTable
from infra.rag_api import LLMRAGAPI


class ElevateBeStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        main_resources_name = os.getenv('RESOURCE_NAME')
        stage = os.getenv('DEPLOYMENT_ENVIRONMENT')

        # DynamoDB Table
        demo_table = dynamodb.Table(
            self,
            f'{main_resources_name}-{stage}-DemoTable',
            table_name=f'{main_resources_name}-{stage}-DemoTable',
            partition_key=dynamodb.Attribute(name='id', type=dynamodb.AttributeType.STRING),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY,
        )

        # Cognito User Pool
        cognito_user_pool = cognito.UserPool(
            self,
            'ElevateUserPool',
            user_pool_name=f'{main_resources_name}-{stage}-UserPool',
            account_recovery=cognito.AccountRecovery.EMAIL_ONLY,
            auto_verify=cognito.AutoVerifiedAttrs(email=True),
            self_sign_up_enabled=True,
            sign_in_aliases=cognito.SignInAliases(email=True),
            mfa=cognito.Mfa.OFF,
            password_policy=cognito.PasswordPolicy(
                min_length=8,
                require_lowercase=True,
                require_digits=True,
                require_symbols=True,
                require_uppercase=True,
                temp_password_validity=Duration.days(7),
            ),
            standard_attributes={'email': cognito.StandardAttribute(mutable=True, required=True)},
            custom_attributes={
                'user_name': cognito.StringAttribute(mutable=True),
                'phone_number': cognito.StringAttribute(mutable=True),
            },
            sign_in_case_sensitive=False,
        )
        cognito_user_pool_client = cognito_user_pool.add_client(
            'UserPoolClient',
            user_pool_client_name=f'{main_resources_name}-{stage}-UserPoolClient',
            auth_flows=cognito.AuthFlow(admin_user_password=True, user_password=True, custom=True, user_srp=True),
            o_auth=cognito.OAuthSettings(
                flows=cognito.OAuthFlows(authorization_code_grant=True, implicit_code_grant=True),
                scopes=[
                    cognito.OAuthScope.PHONE,
                    cognito.OAuthScope.EMAIL,
                    cognito.OAuthScope.OPENID,
                    cognito.OAuthScope.PROFILE,
                    cognito.OAuthScope.COGNITO_ADMIN,
                ],
                callback_urls=['https://cognito.com'],
                logout_urls=['https://cognito.com'],
            ),
            prevent_user_existence_errors=True,
            generate_secret=False,
            refresh_token_validity=Duration.days(180),
            supported_identity_providers=[cognito.UserPoolClientIdentityProvider.COGNITO],
        )

        # User Pool Group - Administrator
        cognito.CfnUserPoolGroup(
            self,
            'UserPoolGroupAdministrator',
            description='Administrator',
            group_name='admin',
            precedence=0,
            user_pool_id=cognito_user_pool.user_pool_id,
        )

        # User Pool Group - Practice Manager
        cognito.CfnUserPoolGroup(
            self,
            'UserPoolGroupPracticeManager',
            description='Super Administrator',
            group_name='super_admin',
            user_pool_id=cognito_user_pool.user_pool_id,
        )

        # LLM RAG API
        entity_table = EntityTable(self, 'EntityTable')
        llm_rag_api = LLMRAGAPI(self, 'LLMRAGAPI', entity_table=entity_table)

        # Appsync API
        api = AppsyncAPI(
            self,
            f'{main_resources_name}-{stage}-appsync-api',
            demo_table=demo_table,
            cognito_user_pool=cognito_user_pool,
            llm_rag_api=llm_rag_api,
            entity_table=entity_table.entity_table,
        )

        # General Bucket
        resource_hash = 'gwzjn89p'
        general_bucket_name = f'{main_resources_name}-{stage}-general-bucket-{resource_hash}'

        general_bucket = s3.Bucket(
            self,
            'GeneralBucket',
            bucket_name=general_bucket_name,
            removal_policy=RemovalPolicy.RETAIN,
            auto_delete_objects=False,
            cors=[
                # TODO: Update to least privelege
                s3.CorsRule(
                    allowed_headers=['*'],
                    allowed_methods=[
                        s3.HttpMethods.GET,
                        s3.HttpMethods.HEAD,
                        s3.HttpMethods.PUT,
                        s3.HttpMethods.POST,
                        s3.HttpMethods.DELETE,
                    ],
                    allowed_origins=['*'],
                    exposed_headers=['x-amz-server-side-encryption', 'x-amz-request-id', 'x-amz-id-2', 'ETag'],
                    max_age=3000,
                )
            ],
        )

        # Cognito Identity Pool for IAM Role-based Authentication
        cognito_identity_pool = cognito.CfnIdentityPool(
            self,
            'ElevateIdentityPool',
            identity_pool_name=f'{main_resources_name}-{stage}-IdentityPool',
            allow_unauthenticated_identities=False,  # Only authenticated users
            cognito_identity_providers=[
                {
                    'clientId': cognito_user_pool_client.user_pool_client_id,
                    'providerName': cognito_user_pool.user_pool_provider_name,
                }
            ],
        )

        # IAM Role for Authenticated Cognito Users
        cognito_authenticated_role = iam.Role(
            self,
            'CognitoAuthenticatedRole',
            role_name=f'{main_resources_name}-{stage}-CognitoAuthenticatedRole',
            assumed_by=iam.FederatedPrincipal(
                'cognito-identity.amazonaws.com',
                {
                    'StringEquals': {'cognito-identity.amazonaws.com:aud': cognito_identity_pool.ref},
                    'ForAnyValue:StringLike': {'cognito-identity.amazonaws.com:amr': 'authenticated'},
                },
                'sts:AssumeRoleWithWebIdentity',
            ),
        )

        # Attach Authenticated Role to Identity Pool
        cognito.CfnIdentityPoolRoleAttachment(
            self,
            'IdentityPoolRoleAttachment',
            identity_pool_id=cognito_identity_pool.ref,
            roles={
                'authenticated': cognito_authenticated_role.role_arn,
            },
        )

        # Attach IAM policy to allow S3 access
        cognito_authenticated_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=['s3:GetObject', 's3:PutObject', 's3:DeleteObject', 's3:ListBucket'],
                resources=[f'{general_bucket.bucket_arn}/*'],
            )
        )

        general_bucket.add_to_resource_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                principals=[iam.ArnPrincipal(cognito_authenticated_role.role_arn)],
                actions=['s3:GetObject', 's3:PutObject', 's3:DeleteObject', 's3:ListBucket'],
                resources=[general_bucket.bucket_arn, f'{general_bucket.bucket_arn}/*'],
            )
        )

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
            value=cognito_identity_pool.attr_id,
        )
