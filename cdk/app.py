#!/usr/bin/env python3
import os

import aws_cdk as cdk

from consuldemocracy.consuldemocracy_stack import ConsuldemocracyStack

# OE AWS Marketplace Patterns Dev
# arn:aws:organizations::440643590597:account/o-kqeqlsvu0w/992593896645
# ~/.aws/config
# [profile oe-patterns-dev]
# region=us-east-1
# role_arn=arn:aws:iam::992593896645:role/OrganizationAccountAccessRole
# source_profile=oe-prod
env_oe_patterns_dev_us_east_1 = cdk.Environment(account="992593896645", region="us-east-1")

app = cdk.App()
ConsuldemocracyStack(
    app,
    "oe-patterns-consuldemocracy-{}".format(os.environ['USER']),
    env=env_oe_patterns_dev_us_east_1,
    synthesizer=cdk.DefaultStackSynthesizer(generate_bootstrap_version_rule=False)
)
app.synth()
