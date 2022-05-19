#!/bin/bash

echo 'test'
success=$?
cfn-signal --exit-code $success --stack ${AWS::StackName} --resource ConsulAsg --region ${AWS::Region}
