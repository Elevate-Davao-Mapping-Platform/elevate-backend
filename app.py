#!/usr/bin/env python3
import os

import aws_cdk as cdk
from dotenv import load_dotenv

from infra.elevate_be_stack import ElevateBeStack

load_dotenv()

main_resources_name = 'elevate'
region = os.getenv('AWS_REGION') or 'ap-southeast-1'
account = os.getenv('CDK_DEFAULT_ACCOUNT')
env = cdk.Environment(account=account, region=region)

app = cdk.App()

# Get configuration from cdk.json context
MAIN_RESOURCES_NAME = app.node.try_get_context('main_resources_name')
STAGE = app.node.try_get_context('stage') or 'dev'

stage = 'dev'
construct_id = f'{main_resources_name}-backend-stack-{stage}'
ElevateBeStack(
    app,
    construct_id=construct_id,
    main_resources_name=main_resources_name,
    stage=stage,
)

stage = 'staging'
construct_id = f'{main_resources_name}-backend-stack-{stage}'
ElevateBeStack(
    app,
    construct_id=construct_id,
    main_resources_name=main_resources_name,
    stage=stage,
)

stage = 'prod'
construct_id = f'{main_resources_name}-backend-stack-{stage}'
ElevateBeStack(
    app,
    construct_id=construct_id,
    main_resources_name=main_resources_name,
    stage=stage,
)

app.synth()
