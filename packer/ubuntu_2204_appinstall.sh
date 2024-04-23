SCRIPT_VERSION=1.3.0
SCRIPT_PREINSTALL=ubuntu_2004_2204_preinstall.sh
SCRIPT_POSTINSTALL=ubuntu_2004_2204_postinstall.sh

# preinstall steps
curl -O "https://raw.githubusercontent.com/ordinaryexperts/aws-marketplace-utilities/$SCRIPT_VERSION/packer_provisioning_scripts/$SCRIPT_PREINSTALL"
chmod +x $SCRIPT_PREINSTALL
./$SCRIPT_PREINSTALL --install-efs-utils
rm $SCRIPT_PREINSTALL

# aws cloudwatch
cat <<EOF > /opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json
{
  "agent": {
    "metrics_collection_interval": 60,
    "run_as_user": "root",
    "logfile": "/opt/aws/amazon-cloudwatch-agent/logs/amazon-cloudwatch-agent.log"
  },
  "metrics": {
    "metrics_collected": {
      "collectd": {
        "metrics_aggregation_interval": 60
      },
      "disk": {
        "measurement": ["used_percent"],
        "metrics_collection_interval": 60,
        "resources": ["*"]
      },
      "mem": {
        "measurement": ["mem_used_percent"],
        "metrics_collection_interval": 60
      }
    },
    "append_dimensions": {
      "ImageId": "\${aws:ImageId}",
      "InstanceId": "\${aws:InstanceId}",
      "InstanceType": "\${aws:InstanceType}",
      "AutoScalingGroupName": "\${aws:AutoScalingGroupName}"
    }
  },
  "logs": {
    "logs_collected": {
      "files": {
        "collect_list": [
          {
            "file_path": "/opt/aws/amazon-cloudwatch-agent/logs/amazon-cloudwatch-agent.log",
            "log_group_name": "ASG_SYSTEM_LOG_GROUP_PLACEHOLDER",
            "log_stream_name": "{instance_id}-/opt/aws/amazon-cloudwatch-agent/logs/amazon-cloudwatch-agent.log",
            "timezone": "UTC"
          },
          {
            "file_path": "/var/log/dpkg.log",
            "log_group_name": "ASG_SYSTEM_LOG_GROUP_PLACEHOLDER",
            "log_stream_name": "{instance_id}-/var/log/dpkg.log",
            "timezone": "UTC"
          },
          {
            "file_path": "/var/log/apt/history.log",
            "log_group_name": "ASG_SYSTEM_LOG_GROUP_PLACEHOLDER",
            "log_stream_name": "{instance_id}-/var/log/apt/history.log",
            "timezone": "UTC"
          },
          {
            "file_path": "/var/log/cloud-init.log",
            "log_group_name": "ASG_SYSTEM_LOG_GROUP_PLACEHOLDER",
            "log_stream_name": "{instance_id}-/var/log/cloud-init.log",
            "timezone": "UTC"
          },
          {
            "file_path": "/var/log/cloud-init-output.log",
            "log_group_name": "ASG_SYSTEM_LOG_GROUP_PLACEHOLDER",
            "log_stream_name": "{instance_id}-/var/log/cloud-init-output.log",
            "timezone": "UTC"
          },
          {
            "file_path": "/var/log/auth.log",
            "log_group_name": "ASG_SYSTEM_LOG_GROUP_PLACEHOLDER",
            "log_stream_name": "{instance_id}-/var/log/auth.log",
            "timezone": "UTC"
          },
          {
            "file_path": "/var/log/syslog",
            "log_group_name": "ASG_SYSTEM_LOG_GROUP_PLACEHOLDER",
            "log_stream_name": "{instance_id}-/var/log/syslog",
            "timezone": "UTC"
          },
          {
            "file_path": "/var/log/amazon/ssm/amazon-ssm-agent.log",
            "log_group_name": "ASG_SYSTEM_LOG_GROUP_PLACEHOLDER",
            "log_stream_name": "{instance_id}-/var/log/amazon/ssm/amazon-ssm-agent.log",
            "timezone": "UTC"
          },
          {
            "file_path": "/var/log/amazon/ssm/errors.log",
            "log_group_name": "ASG_SYSTEM_LOG_GROUP_PLACEHOLDER",
            "log_stream_name": "{instance_id}-/var/log/amazon/ssm/errors.log",
            "timezone": "UTC"
          },
          {
            "file_path": "/home/deploy/consul/shared/log/delayed_job.log",
            "log_group_name": "ASG_APP_LOG_GROUP_PLACEHOLDER",
            "log_stream_name": "{instance_id}-/home/deploy/consul/shared/log/delayed_job.log",
            "timezone": "UTC"
          },
          {
            "file_path": "/home/deploy/consul/shared/log/production.log",
            "log_group_name": "ASG_APP_LOG_GROUP_PLACEHOLDER",
            "log_stream_name": "{instance_id}-/home/deploy/consul/shared/log/production.log",
            "timezone": "UTC"
          },
          {
            "file_path": "/home/deploy/consul/shared/log/puma_access.log",
            "log_group_name": "ASG_APP_LOG_GROUP_PLACEHOLDER",
            "log_stream_name": "{instance_id}-/home/deploy/consul/shared/log/puma_access.log",
            "timezone": "UTC"
          },
          {
            "file_path": "/home/deploy/consul/shared/log/puma_error.log",
            "log_group_name": "ASG_APP_LOG_GROUP_PLACEHOLDER",
            "log_stream_name": "{instance_id}-/home/deploy/consul/shared/log/puma_error.log",
            "timezone": "UTC"
          },
          {
            "file_path": "/var/log/nginx/access.log",
            "log_group_name": "ASG_APP_LOG_GROUP_PLACEHOLDER",
            "log_stream_name": "{instance_id}-/var/log/nginx/access.log",
            "timezone": "UTC"
          },
          {
            "file_path": "/var/log/nginx/error.log",
            "log_group_name": "ASG_APP_LOG_GROUP_PLACEHOLDER",
            "log_stream_name": "{instance_id}-/var/log/nginx/error.log",
            "timezone": "UTC"
          }
        ]
      }
    },
    "log_stream_name": "{instance_id}"
  }
}
EOF

# Start Consul setup
ssh-keygen -b 2048 -t rsa -f /root/.ssh/id_rsa -q -N ""
apt-get -y install libpq-dev
python3 -m pip install ansible psycopg2
git clone https://github.com/consul/installer /root/installer
cd /root/installer
git checkout 2.1.1
printf "[servers]\nlocalhost ansible_user=root\n" > /root/installer/hosts
rm /root/installer/hosts.example
cp -r roles/rails roles/rails_ami
sed -i '33,$d' roles/rails_ami/tasks/main.yml
cat <<EOF > /root/installer/aws_ami.yml
---
- import_playbook: user.yml
- import_playbook: system.yml
- name: Set up CONSUL DEMOCRACY
  hosts: all
  become: true
  become_user: "{{ deploy_user }}"
  vars:
    # https://github.com/ansible/proposals/issues/89
    ansible_user: "{{ deploy_user }}"
  roles:
    - folder_structure
    - ruby
    - nodejs
    - rails_ami

- name: Post-installation tasks
  hosts: all
  become: true
  vars:
    ansible_user: "{{ deploy_user }}"
  roles:
    - memcached
    - timezone
EOF
ansible-playbook -v aws_ami.yml --connection=local -i hosts
echo "gem 'aws-sdk-s3', '~> 1.144'" >> /home/deploy/consul/current/Gemfile_custom
ansible-playbook -v aws_ami.yml --connection=local -i hosts
rm -rf /home/deploy/.ssh
rm -rf /root/.ssh
rm -rf /home/deploy/consul/current/log/*

# https://medium.com/@igkuz/managing-unicorn-puma-with-systemd-93e95f75d1ae
echo "export XDG_RUNTIME_DIR=/run/user/`id -u`" >> /home/deploy/.profile
loginctl enable-linger deploy

apt-get install -y nginx

cp -r roles/rails roles/rails_boot
sed -i '2,87d' roles/rails_boot/tasks/main.yml
cat <<EOF > /root/installer/aws_boot.yml
---
- name: Set up web server
  hosts: all
  become: true
  vars:
    ansible_user: "{{ deploy_user }}"
  roles:
    - nginx
- name: Set up CONSUL DEMOCRACY
  hosts: all
  become: true
  become_user: "{{ deploy_user }}"
  vars:
    # https://github.com/ansible/proposals/issues/89
    ansible_user: "{{ deploy_user }}"
  roles:
    - rails_boot
    - puma
EOF

pip install boto3
cat <<EOF > /root/check-secrets.py
#!/usr/bin/env python3

import boto3
import json
import subprocess
import sys
import uuid

region_name = sys.argv[1]
secret_name = sys.argv[2]

client = boto3.client("secretsmanager", region_name=region_name)
response = client.list_secrets(
  Filters=[{"Key": "name", "Values": [secret_name]}]
)
arn = response["SecretList"][0]["ARN"]
response = client.get_secret_value(
  SecretId=arn
)
current_secret = json.loads(response["SecretString"])
needs_update = False

if not 'secret_key_base' in current_secret:
  needs_update = True
  cmd = "random_value=\$(seed=\$(date +%s%N); tr -dc '[:alnum:]' < /dev/urandom | head -c 64; echo \$seed | sha256sum | awk '{print substr(\$1, 1, 64)}'); echo \$random_value"
  output = subprocess.run(cmd, stdout=subprocess.PIPE, shell=True).stdout.decode('utf-8').strip()
  current_secret['secret_key_base'] = output
if not 'admin_password' in current_secret:
  needs_update = True
  cmd = "random_value=\$(seed=\$(date +%s%N); tr -dc '[:alnum:]' < /dev/urandom | head -c 16; echo \$seed | sha256sum | awk '{print substr(\$1, 1, 16)}'); echo \$random_value"
  output = subprocess.run(cmd, stdout=subprocess.PIPE, shell=True).stdout.decode('utf-8').strip()
  current_secret['admin_password'] = output
if needs_update:
  client.update_secret(
    SecretId=arn,
    SecretString=json.dumps(current_secret)
  )
else:
  print('Secrets already generated - no action needed.')
EOF
chown root:root /root/check-secrets.py
chmod 744 /root/check-secrets.py

cd -
# End Consul setup

# post install steps
curl -O "https://raw.githubusercontent.com/ordinaryexperts/aws-marketplace-utilities/$SCRIPT_VERSION/packer_provisioning_scripts/$SCRIPT_POSTINSTALL"
chmod +x "$SCRIPT_POSTINSTALL"
./"$SCRIPT_POSTINSTALL"
rm $SCRIPT_POSTINSTALL
