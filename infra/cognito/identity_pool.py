from aws_cdk import aws_cognito as cognito
from aws_cdk import aws_iam as iam
from constructs import Construct
from infra.config import Config

class IdentityPoolConstruct(Construct):
    def __init__(
        self,
        scope: Construct,
        id: str,
        config: Config,
        user_pool_client: cognito.UserPoolClient,
        user_pool_provider_name: str,
        **kwargs
    ) -> None:
        super().__init__(scope, id, **kwargs)
        main_resources_name = config.main_resources_name
        stage = config.stage

        # Cognito Identity Pool for IAM Role-based Authentication
        self.identity_pool = cognito.CfnIdentityPool(
            self,
            'ElevateIdentityPool',
            identity_pool_name=f'{main_resources_name}-{stage}-IdentityPool',
            allow_unauthenticated_identities=False,  # Only authenticated users
            cognito_identity_providers=[
                {
                    'clientId': user_pool_client.user_pool_client_id,
                    'providerName': user_pool_provider_name,
                }
            ],
        )

        # IAM Role for Authenticated Cognito Users
        self.authenticated_role = iam.Role(
            self,
            'CognitoAuthenticatedRole',
            role_name=f'{main_resources_name}-{stage}-CognitoAuthenticatedRole',
            assumed_by=iam.FederatedPrincipal(
                'cognito-identity.amazonaws.com',
                {
                    'StringEquals': {'cognito-identity.amazonaws.com:aud': self.identity_pool.ref},
                    'ForAnyValue:StringLike': {'cognito-identity.amazonaws.com:amr': 'authenticated'},
                },
                'sts:AssumeRoleWithWebIdentity',
            ),
        )

        # Attach Authenticated Role to Identity Pool
        cognito.CfnIdentityPoolRoleAttachment(
            self,
            'IdentityPoolRoleAttachment',
            identity_pool_id=self.identity_pool.ref,
            roles={
                'authenticated': self.authenticated_role.role_arn,
            },
        ) 