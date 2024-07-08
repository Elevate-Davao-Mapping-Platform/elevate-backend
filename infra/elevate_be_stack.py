from aws_cdk import Stack, CfnOutput, Duration, CfnParameter, aws_dynamodb as dynamodb, aws_cognito as cognito
from constructs import Construct
from infra.appsync import AppsyncAPI


class ElevateBeStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        project_name = self.node.try_get_context('projectName')
        stage = self.node.try_get_context('stage')
        service_name = self.node.try_get_context('serviceName')

        # DynamoDB Table
        demo_table = dynamodb.Table(
            self,
            f'{project_name}-{stage}-DemoTable',
            partition_key=dynamodb.Attribute(name='id', type=dynamodb.AttributeType.STRING),
        )

        # Cognito User Pool
        cognito_user_pool = cognito.UserPool(
            self,
            'ElevateUserPool',
            user_pool_name=f'{project_name}-{stage}-{service_name}-UserPool',
            account_recovery=cognito.AccountRecovery.EMAIL_ONLY,
            auto_verify=cognito.AutoVerifiedAttrs(email=True),
            self_sign_up_enabled=True,
            sign_in_aliases=cognito.SignInAliases(email=True),
            mfa=cognito.Mfa.OFF,
            password_policy=cognito.PasswordPolicy(
                min_length=8,
                require_lowercase=True,
                require_digits=True,
                require_symbols=False,
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
            user_pool_client_name=f'{project_name}-{stage}-{service_name}-UserPoolClient',
            auth_flows=cognito.AuthFlow(admin_user_password=True, user_password=True, custom=True),
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
            generate_secret=True,
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

        # Appsync API
        api = AppsyncAPI(self, 'AppsyncAPI', demo_table=demo_table, cognito_user_pool=cognito_user_pool)

        # Outputs
        CfnOutput(self, 'GraphQLAPIURL', value=api.graphql_url)
        CfnOutput(self, 'GraphQL API Key', value=api.api_key)
        CfnOutput(
            self,
            'UserPoolId',
            value=cognito_user_pool.user_pool_id,
            export_name=f"UserPoolId-{self.node.try_get_context('stage')}",
        )
        CfnOutput(
            self,
            'AppClientId',
            value=cognito_user_pool_client.user_pool_client_id,
            export_name=f"AppClientId-{self.node.try_get_context('stage')}",
        )
