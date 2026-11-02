#!/usr/bin/env python3
import os
import aws_cdk as cdk
from infrastructure.infrastructure_stack import InfrastructureStack

app = cdk.App()
InfrastructureStack(
    app,
    "InfrastructureStack",
    env=cdk.Environment(
        account=os.getenv("CDK_DEFAULT_ACCOUNT", "535635599092"),
        region=os.getenv("CDK_DEFAULT_REGION", "us-east-1"),
    ),
)
app.synth()
