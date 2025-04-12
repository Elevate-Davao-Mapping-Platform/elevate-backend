from aws_cdk import (
    CfnOutput,
    Duration,
    RemovalPolicy,
    aws_events,
    aws_events_targets,
    aws_iam,
    aws_lambda,
    aws_logs,
)
from aws_cdk.aws_lambda_python_alpha import (
    BundlingOptions,
    PythonFunction,
    PythonLayerVersion,
)
from constructs import Construct

from infra.config import Config
from infra.dynamodb.entity_table import EntityTable


class SuggestionsCron(Construct):
    """
    Class to create the infrastructure on AWS.
    """

    def __init__(self, scope: Construct, id: str, config: Config, **kwargs) -> None:
        self.common_dependencies_layer: PythonLayerVersion = kwargs.pop(
            'common_dependencies_layer', None
        )
        self.entity_table: EntityTable = kwargs.pop('entity_table', None)

        super().__init__(scope, id, **kwargs)

        self.config = config

        self.create_lambda_function()
        self.create_eventbridge_rule()
        self.generate_cloudformation_outputs()

    def create_lambda_function(self):
        """
        Create the Lambda Function for the Suggestions Cron Job
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

        # Grant permission to invoke Bedrock
        lambda_role.add_to_policy(
            aws_iam.PolicyStatement(
                actions=['bedrock:InvokeModel', 'bedrock:InvokeModelWithResponseStream'],
                resources=[
                    'arn:aws:bedrock:*:*:inference-profile/us.anthropic.claude-3-5-haiku-20241022-v1:0',
                    'arn:aws:bedrock:*:*:foundation-model/anthropic.claude-3-5-haiku-20241022-v1:0',
                ],
            )
        )

        lambda_role.add_to_policy(
            aws_iam.PolicyStatement(
                actions=['bedrock:Retrieve'],
                resources=['arn:aws:bedrock:us-east-1:058264295349:knowledge-base/ORGCXIYNDH'],
            )
        )

        lambda_role.add_to_policy(
            aws_iam.PolicyStatement(
                actions=[
                    'dynamodb:Query',
                    'dynamodb:GetItem',
                    'dynamodb:Scan',
                    'dynamodb:BatchWriteItem',
                ],
                resources=[self.entity_table.table_arn],
            )
        )

        # Create the Lambda function using Docker
        self.suggestions_cron_layer = PythonLayerVersion(
            self,
            f'{self.config.prefix}-suggestions-cron-layer',
            layer_version_name=f'{self.config.prefix}-suggestions-cron-layer',
            entry='src/generate_suggestions/layer',
            compatible_runtimes=[aws_lambda.Runtime.PYTHON_3_12],
            compatible_architectures=[aws_lambda.Architecture.X86_64],
            description='Dependencies for Suggestions Cron Job Lambda',
            removal_policy=RemovalPolicy.DESTROY,
            bundling=BundlingOptions(
                asset_excludes=[
                    '**/__pycache__',
                ],
            ),
        )

        self.lambda_suggestions_cron = PythonFunction(
            self,
            f'{self.config.prefix}-suggestions-cron',
            function_name=f'{self.config.prefix}-suggestions-cron',
            runtime=aws_lambda.Runtime.PYTHON_3_12,
            handler='handler',
            entry='src',
            index='generate_suggestions/handler.py',
            timeout=Duration.minutes(2),
            log_retention=aws_logs.RetentionDays.ONE_MONTH,
            memory_size=512,
            environment={
                'STAGE': self.config.stage,
                'LOG_LEVEL': self.config.log_level,
                'REGION': self.config.region,
                'ENTITIES_TABLE': self.entity_table.table_name,
                'BEDROCK_AWS_REGION': self.config.bedrock_region,
                'POWERTOOLS_LOG_LEVEL': 'DEBUG' if self.config.stage == 'dev' else 'INFO',
                'POWERTOOLS_SERVICE_NAME': f'{self.config.prefix}-suggestions-service',
                'POWERTOOLS_LOGGER_LOG_EVENT': 'true' if self.config.stage == 'dev' else 'false',
            },
            role=lambda_role,
            layers=[self.common_dependencies_layer, self.suggestions_cron_layer],
            bundling=BundlingOptions(
                asset_excludes=['**/__pycache__', 'local_tests', 'generate_suggestions', 'rag_api'],
            ),
        )

    def create_eventbridge_rule(self):
        """
        Create an EventBridge rule to trigger the Lambda function at midnight Philippine time (UTC+8)
        """
        ph_time_midnight_utc = '16'

        lambda_schedule = aws_events.Schedule.cron(
            minute='0', hour=ph_time_midnight_utc, day='*', month='*', year='*'
        )

        rule = aws_events.Rule(
            self,
            f'{self.config.prefix}-suggestions-cron-rule',
            schedule=lambda_schedule,
            targets=[aws_events_targets.LambdaFunction(self.lambda_suggestions_cron)],
        )

        # Grant EventBridge permission to invoke the Lambda function
        self.lambda_suggestions_cron.add_permission(
            'AllowEventBridgeInvoke',
            principal=aws_iam.ServicePrincipal('events.amazonaws.com'),
            action='lambda:InvokeFunction',
            source_arn=rule.rule_arn,
        )

    def generate_cloudformation_outputs(self):
        """
        Method to add the relevant CloudFormation outputs.
        """
        CfnOutput(
            self,
            'FunctionArn',
            value=self.lambda_suggestions_cron.function_arn,
            description='Function ARN',
        )
