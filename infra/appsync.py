import os
from os import path

from aws_cdk import aws_appsync as appsync
from aws_cdk import aws_cognito as cognito
from aws_cdk import aws_dynamodb as dynamodb
from constructs import Construct


class AppsyncAPI(Construct):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        # Extract the custom argument
        demo_table: dynamodb.Table = kwargs.pop('demo_table', None)
        cognito_user_pool: cognito.UserPool = kwargs.pop('cognito_user_pool', None)
        llm_rag_api = kwargs.pop('llm_rag_api', None)  # Call the base class constructor
        main_resources_name = os.environ['RESOURCE_NAME']
        stage = os.environ['DEPLOYMENT_ENVIRONMENT']

        super().__init__(scope, construct_id, **kwargs)

        graphql_api_name = f'{main_resources_name}-{stage}-GraphQLApi'

        gql_schema = path.join(path.dirname(__file__), '..', 'schema', 'schema.graphql')

        api = appsync.GraphqlApi(
            self,
            'Api',
            name=graphql_api_name,
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

        demo_dS = api.add_dynamo_db_data_source(f'{main_resources_name}-{stage}-DDBsource', demo_table)

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

        rag_ds = api.add_lambda_data_source('RagApiDataSource', llm_rag_api.lambda_rag_api)

        # Create resolver for the processRagQuery mutation
        rag_ds.create_resolver(
            'MutationProcessRagQuery',
            type_name='Mutation',
            field_name='processRagQuery',
            request_mapping_template=appsync.MappingTemplate.lambda_request(),
            response_mapping_template=appsync.MappingTemplate.lambda_result(),
        )

        # Output values
        self.graphql_url = api.graphql_url
        self.api_key = api.api_key
        self.api_id = api.api_id
