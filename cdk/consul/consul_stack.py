from aws_cdk import (
    # Duration,
    Stack,
    # aws_sqs as sqs,
)
from constructs import Construct

from oe_patterns_cdk_common.asg import Asg
from oe_patterns_cdk_common.vpc import Vpc

class ConsulStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # vpc
        vpc = Vpc(
            self,
            "Vpc"
        )
