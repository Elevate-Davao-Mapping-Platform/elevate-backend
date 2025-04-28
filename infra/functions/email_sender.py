from aws_cdk import (
    CfnOutput,
    Duration,
    aws_iam,
    aws_lambda,
    aws_lambda_event_sources,
    aws_logs,
    aws_sqs,
)
from aws_cdk.aws_lambda_python_alpha import (
    BundlingOptions,
    PythonFunction,
    PythonLayerVersion,
)
from constructs import Construct

from infra.config import Config
from infra.functions.lambda_utils import LambdaUtils


class EmailSender(Construct):
    """
    Class to create the infrastructure for the Email Sender Lambda function.
    """

    def __init__(self, scope: Construct, id: str, config: Config, **kwargs) -> None:
        self.common_dependencies_layer: PythonLayerVersion = kwargs.pop(
            'common_dependencies_layer', None
        )

        super().__init__(scope, id, **kwargs)

        self.config = config

        # Create SQS queue first
        self.create_sqs_queue()

        # Then create the Lambda function
        self.create_lambda_function()
        self.generate_cloudformation_outputs()

    def create_sqs_queue(self):
        """
        Create the SQS queue for email sending requests
        """
        self.email_queue = aws_sqs.Queue(
            self,
            f'{self.config.prefix}-email-queue',
            queue_name=f'{self.config.prefix}-email-queue',
            visibility_timeout=Duration.seconds(300),  # 5 minutes
            retention_period=Duration.days(14),  # Messages retained for 14 days
        )

    def create_lambda_function(self):
        """
        Create the Lambda Function for sending emails via SES
        and create necessary IAM roles and permissions.
        """
        # Define the IAM role
        lambda_role = aws_iam.Role(
            self,
            'LambdaExecutionRole',
            assumed_by=aws_iam.ServicePrincipal('lambda.amazonaws.com'),
            managed_policies=[
                aws_iam.ManagedPolicy.from_aws_managed_policy_name(
                    'service-role/AWSLambdaBasicExecutionRole'
                ),
                aws_iam.ManagedPolicy.from_aws_managed_policy_name(
                    'service-role/AWSLambdaVPCAccessExecutionRole'
                ),
            ],
        )

        # Add SES permissions
        lambda_role.add_to_policy(
            aws_iam.PolicyStatement(actions=['ses:SendEmail', 'ses:SendRawEmail'], resources=['*'])
        )

        # Add SQS permissions
        lambda_role.add_to_policy(
            aws_iam.PolicyStatement(
                actions=['sqs:ReceiveMessage', 'sqs:DeleteMessage', 'sqs:GetQueueAttributes'],
                resources=[self.email_queue.queue_arn],
            )
        )

        self.email_sender_lambda = PythonFunction(
            self,
            f'{self.config.prefix}-email-sender',
            function_name=f'{self.config.prefix}-email-sender',
            runtime=aws_lambda.Runtime.PYTHON_3_12,
            handler='handler',
            entry='src',
            index='email_sender/handler.py',
            timeout=Duration.minutes(5),
            log_retention=aws_logs.RetentionDays.ONE_MONTH,
            memory_size=512,
            environment={
                'STAGE': self.config.stage,
                'LOG_LEVEL': self.config.log_level,
                'REGION': self.config.region,
                'POWERTOOLS_LOG_LEVEL': 'DEBUG' if self.config.stage == 'dev' else 'INFO',
                'POWERTOOLS_SERVICE_NAME': f'{self.config.prefix}-email-sender-service',
                'POWERTOOLS_LOGGER_LOG_EVENT': 'true' if self.config.stage == 'dev' else 'false',
            },
            role=lambda_role,
            layers=[self.common_dependencies_layer],
            bundling=BundlingOptions(
                asset_excludes=LambdaUtils.get_asset_excludes(
                    included_folders=['email_sender', 'shared_modules']
                ),
            ),
        )

        # Add SQS trigger
        self.email_sender_lambda.add_event_source(
            aws_lambda_event_sources.SqsEventSource(
                self.email_queue,
                batch_size=1,
            )
        )

    def generate_cloudformation_outputs(self):
        """
        Method to add the relevant CloudFormation outputs.
        """
        CfnOutput(
            self,
            'FunctionArn',
            value=self.email_sender_lambda.function_arn,
            description='Function ARN',
        )

        CfnOutput(
            self,
            'QueueUrl',
            value=self.email_queue.queue_url,
            description='SQS Queue URL',
        )
