#!/bin/bash

cd /root/installer
ansible-playbook -v consul.yml --connection=local -i hosts
success=$?
cfn-signal --exit-code $success --stack ${AWS::StackName} --resource Asg --region ${AWS::Region}
