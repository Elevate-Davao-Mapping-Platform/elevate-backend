#!/usr/bin/env python3
import os

import aws_cdk as cdk

from infra.elevate_be_stack import ElevateBeStack

app = cdk.App()

main_resources_name = 'elevate-backend-stack'
os.environ['RESOURCE_NAME'] = main_resources_name

stage = app.node.try_get_context('stage')
os.environ['DEPLOYMENT_ENVIRONMENT'] = stage
os.environ['AWS_REGION'] = 'ap-southeast-1'

construct_id = f'{main_resources_name}-{stage}'

ElevateBeStack(
    app,
    construct_id=construct_id,
)

app.synth()
