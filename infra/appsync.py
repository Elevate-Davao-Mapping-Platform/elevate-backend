from os import path
from aws_cdk import (
    aws_appsync as appsync,
    aws_dynamodb as dynamodb,
    aws_cognito as cognito,
)
from constructs import Construct


class AppsyncAPI(Construct):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        # Extract the custom argument
        demo_table: dynamodb.Table = kwargs.pop('demo_table', None)
        cognito_user_pool: cognito.UserPool = kwargs.pop('cognito_user_pool', None)

        # Call the base class constructor
        super().__init__(scope, construct_id, **kwargs)

        gql_schema = path.join(path.dirname(__file__), '..', 'schema', 'schema.graphql')

        api = appsync.GraphqlApi(
            self,
            'Api',
            name='demo',
            definition=appsync.Definition.from_file(gql_schema),
            authorization_config=appsync.AuthorizationConfig(
                default_authorization=appsync.AuthorizationMode(authorization_type=appsync.AuthorizationType.API_KEY),
                additional_authorization_modes=[
                    appsync.AuthorizationMode(
                        authorization_type=appsync.AuthorizationType.USER_POOL,
                        user_pool_config=appsync.UserPoolConfig(
                            user_pool=cognito_user_pool,
                        ),
                    ),
                ],
            ),
            xray_enabled=True,
        )

        demo_dS = api.add_dynamo_db_data_source('demoDataSource', demo_table)

        # Resolver for the Query "getDemos" that scans the DynamoDb table and returns the entire list.
        demo_dS.create_resolver(
            'QueryGetDemosResolver',
            type_name='Query',
            field_name='getDemos',
            request_mapping_template=appsync.MappingTemplate.dynamo_db_scan_table(),
            response_mapping_template=appsync.MappingTemplate.dynamo_db_result_list(),
        )

        # Resolver for the Mutation "addDemo" that puts the item into the DynamoDb table.
        demo_dS.create_resolver(
            'MutationAddDemoResolver',
            type_name='Mutation',
            field_name='addDemo',
            request_mapping_template=appsync.MappingTemplate.dynamo_db_put_item(
                appsync.PrimaryKey.partition('id').auto(),
                appsync.Values.projecting('input'),
            ),
            response_mapping_template=appsync.MappingTemplate.dynamo_db_result_item(),
        )

        # To enable DynamoDB read consistency with the `MappingTemplate`:
        demo_dS.create_resolver(
            'QueryGetDemosConsistentResolver',
            type_name='Query',
            field_name='getDemosConsistent',
            request_mapping_template=appsync.MappingTemplate.dynamo_db_scan_table(True),
            response_mapping_template=appsync.MappingTemplate.dynamo_db_result_list(),
        )

        # Output values
        self.graphql_url = api.graphql_url
        self.api_key = api.api_key
