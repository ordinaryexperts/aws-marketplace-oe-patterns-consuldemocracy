#!/bin/bash

# aws cloudwatch
sed -i 's/ASG_APP_LOG_GROUP_PLACEHOLDER/${AsgAppLogGroup}/g' /opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json
sed -i 's/ASG_SYSTEM_LOG_GROUP_PLACEHOLDER/${AsgSystemLogGroup}/g' /opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json
systemctl enable amazon-cloudwatch-agent
systemctl start amazon-cloudwatch-agent

# reprovision if access key is rotated
# access key serial: ${SesInstanceUserAccessKeySerial}

mkdir -p /opt/oe/patterns

# secretsmanager
SECRET_ARN="${DbSecretArn}"
echo $SECRET_ARN > /opt/oe/patterns/secret-arn.txt
SECRET_NAME=$(aws secretsmanager list-secrets --query "SecretList[?ARN=='$SECRET_ARN'].Name" --output text)
echo $SECRET_NAME > /opt/oe/patterns/secret-name.txt

aws ssm get-parameter \
    --name "/aws/reference/secretsmanager/$SECRET_NAME" \
    --with-decryption \
    --query Parameter.Value \
| jq -r . > /opt/oe/patterns/secret.json

DB_PASSWORD=$(cat /opt/oe/patterns/secret.json | jq -r .password)
DB_USERNAME=$(cat /opt/oe/patterns/secret.json | jq -r .username)

mkdir -p /etc/letsencrypt/live/${Hostname}
openssl req -x509 -nodes -days 3650 -newkey rsa:2048 \
  -keyout /etc/letsencrypt/live/${Hostname}/privkey.pem \
  -out /etc/letsencrypt/live/${Hostname}/fullchain.pem \
  -subj '/CN=localhost'
cp /root/installer/roles/letsencrypt/templates/options-ssl-nginx.conf /etc/letsencrypt/options-ssl-nginx.conf
openssl dhparam -out /etc/letsencrypt/ssl-dhparams.pem 2048

aws ssm get-parameter \
    --name "/aws/reference/secretsmanager/${InstanceSecretName}" \
    --with-decryption \
    --query Parameter.Value \
| jq -r . > /opt/oe/patterns/instance.json

ACCESS_KEY_ID=$(cat /opt/oe/patterns/instance.json | jq -r .access_key_id)
SECRET_ACCESS_KEY=$(cat /opt/oe/patterns/instance.json | jq -r .secret_access_key)
SMTP_PASSWORD=$(cat /opt/oe/patterns/instance.json | jq -r .smtp_password)

cat <<EOF > /home/deploy/consul/shared/config/database.yml
default: &default
  adapter: postgresql
  encoding: unicode
  host: ${DbCluster.Endpoint.Address}
  pool: 5
  schema_search_path: "public,shared_extensions"
  username: $DB_USERNAME
  password: $DB_PASSWORD

production:
  <<: *default
  database: consul_production
EOF
cat <<EOF > /home/deploy/consul/shared/config/secrets.yml
aps: &maps
  map_tiles_provider: "//{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
  map_tiles_provider_attribution: "&copy; <a href=\"http://osm.org/copyright\">OpenStreetMap</a> contributors"

apis: &apis
  microsoft_api_key: ""
  census_api_end_point: ""
  census_api_institution_code: ""
  census_api_portal_name: ""
  census_api_user_code: ""
  sms_end_point:  ""
  sms_username: ""
  sms_password: ""

http_basic_auth: &http_basic_auth
  http_basic_auth: true

production:
  secret_key_base: "asdflaskjfdlsakjfdsakjfdsadlkfjsaddfkjlsajfaddslkjfdsadlkfjdsadlfkjsadfdlksajdf"
  server_name: "${Hostname}"
  # time_zone: ""
  mailer_delivery_method: :smtp
  smtp_settings:
    :address: "email-smtp.${AWS::Region}.amazonaws.com"
    :port: 587
    :domain: "${HostedZoneName}"
    :user_name: "$ACCESS_KEY_ID"
    :password: "$SMTP_PASSWORD"
    :authentication: "plain"
    :enable_starttls_auto: true
  force_ssl: true
  delay_jobs: true
  errbit_host: ""
  errbit_project_key: ""
  errbit_project_id: 1
  errbit_self_hosted_ssl: false
  http_basic_username: ""
  http_basic_password: ""
  authentication_logs: false
  devise_lockable: false
  managers_url: ""
  managers_application_key: ""
  multitenancy: false
  security:
    last_sign_in: false
    password_complexity: false
    # lockable:
      # maximum_attempts: 20
      # unlock_in: 1 # In hours
  tenants:
    # If you've enabled multitenancy, you can overwrite secrets for a
    # specific tenant with:
    #
    # my_tenant_subdomain:
    #   secret_key: my_secret_value
    #
    # Currently you can overwrite SMTP, SMS, manager, microsoft API,
    # HTTP basic, twitter, facebook, google, wordpress and security settings.
  twitter_key: ""
  twitter_secret: ""
  facebook_key: ""
  facebook_secret: ""
  google_oauth2_key: ""
  google_oauth2_secret: ""
  wordpress_oauth2_key: ""
  wordpress_oauth2_secret: ""
  wordpress_oauth2_site: ""
  <<: *maps
  <<: *apis
EOF

ln -s /home/deploy/consul/shared/config/database.yml /home/deploy/consul/current/config/database.yml
ln -s /home/deploy/consul/shared/config/secrets.yml /home/deploy/consul/current/config/secrets.yml

cd /root/installer
sed -i 's/#domain: your_domain.com/domain: ${Hostname}/' group_vars/all
ansible-playbook -v aws_boot.yml --connection=local -i hosts
success=$?
cfn-signal --exit-code $success --stack ${AWS::StackName} --resource Asg --region ${AWS::Region}
