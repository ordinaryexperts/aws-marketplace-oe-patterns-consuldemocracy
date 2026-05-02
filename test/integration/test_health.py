"""
Health and basic connectivity tests for Consul Democracy.
These tests validate infrastructure and basic application health.
"""

import pytest
import requests


class TestConsulDemocracyHealth:
    """Level 1: Infrastructure and basic health tests."""

    def test_https_accessible(self, base_url):
        """Test that the site is accessible over HTTPS."""
        response = requests.get(base_url, timeout=30, allow_redirects=True)
        assert response.status_code == 200, \
            f"Failed to access Consul Democracy at {base_url}"
        assert response.url.startswith("https://"), \
            "Consul Democracy should be accessible via HTTPS"

    def test_elb_health_endpoint(self, base_url):
        """Test the ALB health-check endpoint used by the load balancer."""
        health_url = f"{base_url}/elb-check"
        response = requests.get(health_url, timeout=10)

        assert response.status_code == 200, \
            f"Health check failed with status {response.status_code}"

    def test_homepage_branding(self, base_url):
        """Test that the homepage renders Consul Democracy branding."""
        response = requests.get(base_url, timeout=30, allow_redirects=True)
        assert response.status_code == 200

        # Consul Democracy renders "CONSUL" prominently in the default skin;
        # also verify Rails CSRF token presence to confirm the Rails app is
        # actually serving the page (not a static error / nginx default).
        body_lower = response.text.lower()
        assert "consul" in body_lower, \
            "Homepage missing 'consul' branding"
        assert 'name="csrf-token"' in response.text, \
            "Homepage missing Rails CSRF token meta tag - app may not be running"

    def test_login_page_present(self, base_url):
        """Test that the login entry point is reachable."""
        login_url = f"{base_url}/users/sign_in"
        response = requests.get(login_url, timeout=10, allow_redirects=True)

        assert response.status_code == 200, \
            f"Login page returned status {response.status_code}"
        assert "sign in" in response.text.lower() or "log in" in response.text.lower(), \
            "Login page missing expected sign-in text"

    def test_response_time(self, base_url):
        """Test that the app responds within acceptable time."""
        import time

        start = time.time()
        response = requests.get(f"{base_url}/elb-check", timeout=30)
        elapsed = time.time() - start

        assert response.status_code == 200, "Health check failed"
        assert elapsed < 5.0, \
            f"Response time {elapsed:.2f}s exceeds 5 seconds"

    def test_ssl_certificate(self, base_url):
        """Verify SSL certificate is valid."""
        import ssl
        import socket
        from urllib.parse import urlparse

        parsed = urlparse(base_url)
        hostname = parsed.hostname
        port = parsed.port or 443

        context = ssl.create_default_context()
        try:
            with socket.create_connection((hostname, port), timeout=10) as sock:
                with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                    cert = ssock.getpeercert()
                    assert cert is not None, "No SSL certificate found"
        except ssl.SSLError as e:
            pytest.fail(f"SSL certificate validation failed: {e}")


class TestConsulDemocracyInfrastructure:
    """Level 2: AWS infrastructure tests."""

    def test_cloudformation_stack_exists(self, cloudformation_client, stack_name):
        """Verify CloudFormation stack exists and is in good state."""
        response = cloudformation_client.describe_stacks(StackName=stack_name)

        assert len(response["Stacks"]) == 1, \
            f"Expected 1 stack, found {len(response['Stacks'])}"

        stack = response["Stacks"][0]
        assert stack["StackStatus"] in ["CREATE_COMPLETE", "UPDATE_COMPLETE"], \
            f"Stack is in unexpected state: {stack['StackStatus']}"

    def test_stack_outputs(self, stack_outputs):
        """Verify CloudFormation stack has required outputs."""
        required_outputs = [
            "DnsSiteUrlOutput",
            "VpcIdOutput",
        ]

        for output in required_outputs:
            assert output in stack_outputs, \
                f"Required output '{output}' missing from stack"
            assert stack_outputs[output], \
                f"Output '{output}' is empty"

    def test_ec2_instance_running(self, instance_id, ec2_client):
        """Verify EC2 instance is running."""
        response = ec2_client.describe_instances(InstanceIds=[instance_id])

        assert len(response["Reservations"]) > 0, \
            f"No reservations found for instance {instance_id}"

        instance = response["Reservations"][0]["Instances"][0]
        assert instance["State"]["Name"] == "running", \
            f"Instance is not running: {instance['State']['Name']}"
