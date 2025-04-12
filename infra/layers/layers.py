from aws_cdk import RemovalPolicy, aws_lambda
from aws_cdk.aws_lambda_python_alpha import BundlingOptions, PythonLayerVersion
from constructs import Construct

from infra.config import Config


class CommonDependenciesLayer(Construct):
    """
    Class to create the infrastructure on AWS.
    """

    def __init__(self, scope: Construct, id: str, config: Config, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        self.config = config

        self.create_layer()

    def create_layer(self):
        """
        Create the Common Dependencies Layer
        """
        self.common_dependencies_layer = PythonLayerVersion(
            self,
            f'{self.config.prefix}-common-dependencies-layer',
            layer_version_name=f'{self.config.prefix}-common-dependencies-layer',
            entry='infra/layers/common_dependencies',
            compatible_runtimes=[aws_lambda.Runtime.PYTHON_3_12],
            compatible_architectures=[aws_lambda.Architecture.X86_64],
            description='Common dependencies for all Lambda functions',
            removal_policy=RemovalPolicy.DESTROY,
            bundling=BundlingOptions(
                asset_excludes=[
                    '**/__pycache__',
                ],
            ),
        )

    def get_layer(self) -> PythonLayerVersion:
        """
        Get the Common Dependencies Layer
        """
        return self.common_dependencies_layer
