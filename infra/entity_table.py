import os
from aws_cdk import aws_dynamodb as dynamodb, RemovalPolicy
from constructs import Construct

class EntityTable(Construct):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id)

        main_resources_name = os.getenv('RESOURCE_NAME')
        stage = os.getenv('DEPLOYMENT_ENVIRONMENT')

        self.table_name = f'{main_resources_name}-{stage}-EntityTable'
        self.entity_table = dynamodb.Table(
            self,
            self.table_name,
            table_name=self.table_name,
            partition_key=dynamodb.Attribute(name='hashKey', type=dynamodb.AttributeType.STRING),
            sort_key=dynamodb.Attribute(name='rangeKey', type=dynamodb.AttributeType.STRING),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY,
        )
        self.table_arn = self.entity_table.table_arn
        