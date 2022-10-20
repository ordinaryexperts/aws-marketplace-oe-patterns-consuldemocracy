from aws_cdk import (
    aws_ec2,
    aws_elasticloadbalancingv2,
    aws_logs,
    Aws,
    CfnDeletionPolicy,
    CfnMapping,
    CfnParameter,
    Stack,
    Tags
)
from constructs import Construct

from oe_patterns_cdk_common.alb import Alb
from oe_patterns_cdk_common.asg import Asg
from oe_patterns_cdk_common.dns import Dns
from oe_patterns_cdk_common.vpc import Vpc

AMI_ID="ami-0e5d873024f9f82f3"
AMI_NAME="ordinary-experts-patterns-consul--20220819-0303"
generated_ami_ids = {
    "us-east-1": "ami-0e5d873024f9f82f3"
}
# End generated code block.

class ConsulStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # vpc
        vpc = Vpc(
            self,
            "Vpc"
        )

        # asg
        with open("consul/launch_config_user_data.sh") as f:
            launch_config_user_data = f.read()
        asg = Asg(
            self,
            "Asg",
            allow_associate_address = True,
            data_volume_size = 100,
            singleton = True,
            default_instance_type = "t3.xlarge",
            user_data_contents = launch_config_user_data,
            user_data_variables = {},
            vpc = vpc
        )

        ami_mapping={
            "AMI": {
                "OECONSUL": AMI_NAME
            }
        }
        for region in generated_ami_ids.keys():
            ami_mapping[region] = { "AMI": generated_ami_ids[region] }
        aws_ami_region_map = CfnMapping(
            self,
            "AWSAMIRegionMap",
            mapping=ami_mapping
        )


        alb = Alb(self, "Alb", asg=asg, vpc=vpc, target_group_https = False)
        asg.asg.target_group_arns = [ alb.target_group.ref ]

        dns = Dns(self, "Dns", alb=alb)
