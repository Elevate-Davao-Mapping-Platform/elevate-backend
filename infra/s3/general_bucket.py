from aws_cdk import RemovalPolicy
from aws_cdk import aws_iam as iam
from aws_cdk import aws_s3 as s3
from constructs import Construct

from infra.config import Config


class GeneralBucketConstruct(Construct):
    def __init__(
        self, scope: Construct, id: str, config: Config, resource_hash: str = 'gwzjn89p', **kwargs
    ) -> None:
        super().__init__(scope, id, **kwargs)

        main_resources_name = config.main_resources_name
        stage = config.stage

        bucket_name = f'{main_resources_name}-{stage}-general-bucket-{resource_hash}'

        self.bucket = s3.Bucket(
            self,
            'GeneralBucket',
            bucket_name=bucket_name,
            removal_policy=RemovalPolicy.RETAIN,
            auto_delete_objects=False,
            cors=[
                # TODO: Update to least privilege
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
                    exposed_headers=[
                        'x-amz-server-side-encryption',
                        'x-amz-request-id',
                        'x-amz-id-2',
                        'ETag',
                    ],
                    max_age=3000,
                )
            ],
        )

    def add_cognito_access(self, cognito_authenticated_role: iam.Role) -> None:
        """Add Cognito user access to the bucket"""
        # Attach IAM policy to allow S3 access
        cognito_authenticated_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=['s3:GetObject', 's3:PutObject', 's3:DeleteObject', 's3:ListBucket'],
                resources=[f'{self.bucket.bucket_arn}/*'],
            )
        )

        self.bucket.add_to_resource_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                principals=[iam.ArnPrincipal(cognito_authenticated_role.role_arn)],
                actions=['s3:GetObject', 's3:PutObject', 's3:DeleteObject', 's3:ListBucket'],
                resources=[self.bucket.bucket_arn, f'{self.bucket.bucket_arn}/*'],
            )
        )
