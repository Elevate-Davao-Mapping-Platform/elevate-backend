from aws_cdk import RemovalPolicy
from aws_cdk import aws_dynamodb as dynamodb
from constructs import Construct

from infra.config import Config


class EntityTable(Construct):
    def __init__(self, scope: Construct, construct_id: str, config: Config, **kwargs) -> None:
        super().__init__(scope, construct_id)

        main_resources_name = config.main_resources_name
        stage = config.stage

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
        self.entity_table.add_global_secondary_index(
            index_name='GSI1PK',
            partition_key=dynamodb.Attribute(name='GSI1PK', type=dynamodb.AttributeType.STRING),
            projection_type=dynamodb.ProjectionType.ALL,
            sort_key=dynamodb.Attribute(name='rangeKey', type=dynamodb.AttributeType.STRING),
        )
        self.entity_table.add_global_secondary_index(
            index_name='GSI2PK',
            partition_key=dynamodb.Attribute(name='GSI2PK', type=dynamodb.AttributeType.STRING),
            projection_type=dynamodb.ProjectionType.ALL,
            sort_key=dynamodb.Attribute(name='rangeKey', type=dynamodb.AttributeType.STRING),
        )

        self.table_arn = self.entity_table.table_arn
