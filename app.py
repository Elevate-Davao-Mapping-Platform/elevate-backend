#!/usr/bin/env python3
import aws_cdk as cdk

from infra.elevate_be_stack import ElevateBeStack


app = cdk.App()

# Dev
ElevateBeStack(
    app,
    f'elevate-backend-stack-dev',
)

# stage
ElevateBeStack(
    app,
    'elevate-backend-stack-stage',
)

# Prod
ElevateBeStack(
    app,
    'elevate-backend-stack-prod',
)

app.synth()
