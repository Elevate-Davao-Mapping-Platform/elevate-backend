from aws_cdk import Duration
from aws_cdk import aws_cognito as cognito
from constructs import Construct

from infra.config import Config


class UserPoolConstruct(Construct):
    def __init__(self, scope: Construct, id: str, config: Config, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        main_resources_name = config.main_resources_name
        stage = config.stage

        # Cognito User Pool
        self.user_pool = cognito.UserPool(
            self,
            'ElevateUserPool',
            user_pool_name=f'{main_resources_name}-{stage}-UserPool-2',
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
                'entity_id': cognito.StringAttribute(mutable=True),
                'user_name': cognito.StringAttribute(mutable=True),
                'role': cognito.StringAttribute(mutable=False),
                'is_first_sign_in': cognito.BooleanAttribute(mutable=True),
            },
            sign_in_case_sensitive=False,
            email=cognito.UserPoolEmail.with_ses(
                from_email=config.app_email,
                from_name=config.app_name,
                reply_to=config.app_email,
                ses_region=config.region,
                ses_verified_domain=config.verified_domain,
            ),
            user_verification=cognito.UserVerificationConfig(
                email_subject='Elevate Davao - Verify Your Email',
                email_body="""
                    Welcome to Elevate Davao!

                    We're excited to have you on board. To complete your registration, please verify your email by entering the following OTP:

                    {####}

                    This code is valid for a limited time, so be sure to enter it soon.

                    If you didn't sign up for Elevate Davao, please ignore this email.

                    Looking forward to seeing you in the community!

                    — The Elevate Davao Team
                """,
                email_style=cognito.VerificationEmailStyle.CODE,
            ),
        )

        # User Pool Client
        self.user_pool_client = self.user_pool.add_client(
            'UserPoolClient',
            user_pool_client_name=f'{main_resources_name}-{stage}-UserPoolClient',
            auth_flows=cognito.AuthFlow(
                admin_user_password=True, user_password=True, custom=True, user_srp=True
            ),
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

        # User Pool Groups
        cognito.CfnUserPoolGroup(
            self,
            'UserPoolGroupAdministrator',
            description='Administrator',
            group_name='admin',
            precedence=0,
            user_pool_id=self.user_pool.user_pool_id,
        )

        cognito.CfnUserPoolGroup(
            self,
            'UserPoolGroupPracticeManager',
            description='Super Administrator',
            group_name='super_admin',
            user_pool_id=self.user_pool.user_pool_id,
        )
