from aws_cdk import Stack, CfnOutput, aws_dynamodb as dynamodb
from constructs import Construct
from infra.appsync import AppsyncAPI


class ElevateBeStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        demo_table = dynamodb.Table(
            self,
            "DemoTable",
            partition_key=dynamodb.Attribute(
                name="id", type=dynamodb.AttributeType.STRING
            ),
        )
        api = AppsyncAPI(self, "AppsyncAPI", demo_table=demo_table)

        CfnOutput(self, "GraphQLAPIURL", value=api.graphql_url)
        CfnOutput(self, "GraphQL API Key", value=api.api_key)
