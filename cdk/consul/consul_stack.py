import os
import subprocess

from aws_cdk import (
    Aws,
    CfnCondition,
    CfnMapping,
    CfnOutput,
    CfnParameter,
    Fn,
    Stack,
    Token
)
from constructs import Construct

from oe_patterns_cdk_common.alb import Alb
from oe_patterns_cdk_common.asg import Asg
from oe_patterns_cdk_common.assets_bucket import AssetsBucket
from oe_patterns_cdk_common.aurora_cluster import AuroraPostgresql
from oe_patterns_cdk_common.db_secret import DbSecret
from oe_patterns_cdk_common.dns import Dns
from oe_patterns_cdk_common.ses import Ses
from oe_patterns_cdk_common.util import Util
from oe_patterns_cdk_common.vpc import Vpc

if "TEMPLATE_VERSION" in os.environ:
    template_version = os.environ["TEMPLATE_VERSION"]
else:
    try:
        template_version = subprocess.check_output(["git", "describe", "--always"]).strip().decode('ascii')
    except:
        template_version = "CICD"

AMI_ID="ami-0f012f80434477427"
AMI_NAME="ordinary-experts-patterns-consul-b575456-20240422-1150"
generated_ami_ids = {
    "us-east-1": "ami-0f012f80434477427"
}
# End generated code block.

class ConsulStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.admin_email_param = CfnParameter(
            self,
            "AdminEmail",
            default="",
            description="Optional: The email address to use for the Consul administrator account. If not specified, 'admin@{DnsHostname}' wil be used."
        )

        self.admin_email_condition = CfnCondition(
            self,
            "AdminEmailCondition",
            expression=Fn.condition_not(Fn.condition_equals(self.admin_email_param.value, ""))
        )

        # vpc
        vpc = Vpc(
            self,
            "Vpc"
        )

        dns = Dns(self, "Dns")

        bucket = AssetsBucket(
            self,
            "AssetsBucket"
        )

        ses = Ses(
            self,
            "Ses",
            hosted_zone_name=dns.route_53_hosted_zone_name_param.value_as_string,
            additional_iam_user_policies=[bucket.user_policy]
        )

        db_secret = DbSecret(
            self,
            "DbSecret"
        )

        db = AuroraPostgresql(
            self,
            "Db",
            database_name="consul_production",
            db_secret=db_secret,
            vpc=vpc
        )

        with open("consul/user_data.sh") as f:
            user_data = f.read()
        asg = Asg(
            self,
            "Asg",
            allow_update_secret = True,
            secret_arns=[db_secret.secret_arn(), ses.secret_arn()],
            default_instance_type = "t3.xlarge",
            use_graviton = False,
            user_data_contents = user_data,
            user_data_variables={
                "AssetsBucketName": bucket.bucket_name(),
                "DbSecretArn": db_secret.secret_arn(),
                "Hostname": dns.hostname(),
                "HostedZoneName": dns.route_53_hosted_zone_name_param.value_as_string,
                "InstanceSecretName": Aws.STACK_NAME + "/instance/credentials"
            },
            vpc = vpc
        )
        asg.asg.node.add_dependency(db.db_primary_instance)
        Util.add_sg_ingress(db, asg.sg)

        ami_mapping={
            "AMI": {
                "OECONSUL": AMI_NAME
            }
        }
        for region in generated_ami_ids.keys():
            ami_mapping[region] = { "AMI": generated_ami_ids[region] }
        CfnMapping(
            self,
            "AWSAMIRegionMap",
            mapping=ami_mapping
        )

        alb = Alb(
            self,
            "Alb",
            asg=asg,
            health_check_path = "/elb-check",
            vpc=vpc
        )
        asg.asg.target_group_arns = [ alb.target_group.ref ]

        dns.add_alb(alb)
        CfnOutput(
            self,
            "FirstUseInstructions",
            description="Instructions for getting started",
            value=f"Click on the DnsSiteUrlOutput link and log in with username of the value of AdminEmailOutput and password of the value of 'admin_password' in the {Aws.STACK_NAME}/instance/credentials secret in Secrets Manager."
        )

        CfnOutput(
            self,
            "AdminEmailOutput",
            description="Email for initial admin user",
            value=Token.as_string(
                Fn.condition_if(
                    self.admin_email_condition.logical_id,
                    self.admin_email_param.value_as_string,
                    f"admin@{dns.route_53_hosted_zone_name_param.value_as_string}"
                )
            )
        )

        parameter_groups = [
            {
                "Label": {
                    "default": "Application Config"
                },
                "Parameters": [
                    self.admin_email_param.logical_id
                ]
            }
        ]
        parameter_groups += alb.metadata_parameter_group()
        parameter_groups += bucket.metadata_parameter_group()
        parameter_groups += db_secret.metadata_parameter_group()
        parameter_groups += db.metadata_parameter_group()
        parameter_groups += dns.metadata_parameter_group()
        parameter_groups += asg.metadata_parameter_group()
        parameter_groups += vpc.metadata_parameter_group()

        # AWS::CloudFormation::Interface
        self.template_options.metadata = {
            "OE::Patterns::TemplateVersion": template_version,
            "AWS::CloudFormation::Interface": {
                "ParameterGroups": parameter_groups,
                "ParameterLabels": {
                    self.admin_email_param.logical_id: {
                        "default": "Consul Admin Email"
                    },
                    **alb.metadata_parameter_labels(),
                    **bucket.metadata_parameter_labels(),
                    **db_secret.metadata_parameter_labels(),
                    **db.metadata_parameter_labels(),
                    **dns.metadata_parameter_labels(),
                    **asg.metadata_parameter_labels(),
                    **vpc.metadata_parameter_labels()
                }
            }
        }
