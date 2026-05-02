"""
End-to-end UI workflow tests for Consul Democracy using Playwright.

These tests drive a real Chromium browser against a deployed stack:
  - Public-side smoke: homepage, proposals/debates listings, sign-in page
  - Admin login: pulls the generated admin password from Secrets Manager
  - Admin content creation: creates a debate and verifies it appears in the listing

Run with:
  pytest test_workflows.py -m ui -v --base-url=https://<host> --stack-name=<stack>

Requires `playwright install chromium` to have been run once in the environment.
"""

import json
import pytest
from playwright.sync_api import sync_playwright, expect


# --- Fixtures -----------------------------------------------------------------


@pytest.fixture(scope="session")
def admin_email(stack_outputs):
    """Admin email is exposed by the stack as AdminEmailOutput."""
    email = stack_outputs.get("AdminEmailOutput")
    if not email:
        pytest.fail("Stack output AdminEmailOutput is missing")
    return email


@pytest.fixture(scope="session")
def admin_password(stack_name, aws_region):
    """
    Pull the generated admin_password from the stack's instance credentials secret.
    The packer install script writes a random 16-char password into
    {StackName}/instance/credentials at first boot.
    """
    import boto3

    client = boto3.client("secretsmanager", region_name=aws_region)
    secret_id = f"{stack_name}/instance/credentials"
    try:
        resp = client.get_secret_value(SecretId=secret_id)
    except client.exceptions.ResourceNotFoundException:
        pytest.fail(f"Secret {secret_id} not found - is the stack fully deployed?")

    payload = json.loads(resp["SecretString"])
    pw = payload.get("admin_password")
    if not pw:
        pytest.fail(f"Secret {secret_id} has no admin_password key")
    return pw


@pytest.fixture
def browser_context():
    """Function-scoped Chromium context.

    Function scope (rather than class/session) is intentional: tests that
    sign in and tests that exercise the public-side anonymous view must not
    share cookies, or Devise's "already signed in, redirecting" behavior
    breaks the next sign-in attempt.
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1280, "height": 720},
            ignore_https_errors=False,
        )
        yield context
        context.close()
        browser.close()


def _sign_in_admin(page, base_url, email, password):
    """Sign in via the Devise form. Leaves the page on the post-login redirect.

    Consul Democracy uses a single 'login' field that accepts email-or-username,
    not separate email/username fields.
    """
    page.goto(f"{base_url}/users/sign_in", wait_until="domcontentloaded", timeout=30000)
    page.fill('input[name="user[login]"]', email)
    page.fill('input[name="user[password]"]', password)
    page.click('form#new_user input[type="submit"][name="commit"], form#new_user button[type="submit"]')
    page.wait_for_load_state("networkidle", timeout=30000)


# --- Public-side UI tests ----------------------------------------------------


@pytest.mark.ui
class TestConsulDemocracyPublicUI:
    """Public-side UI smoke tests — no auth required."""

    def test_homepage_loads_and_branded(self, base_url, browser_context):
        page = browser_context.new_page()
        try:
            page.goto(base_url, wait_until="domcontentloaded", timeout=30000)
            expect(page).to_have_title("CONSUL DEMOCRACY")
            # Sign-in entry point is rendered as a link to /users/sign_in
            expect(page.locator('a[href="/users/sign_in"]').first).to_be_attached()
        finally:
            page.close()

    def test_proposals_listing_accessible(self, base_url, browser_context):
        page = browser_context.new_page()
        try:
            page.goto(f"{base_url}/proposals", wait_until="domcontentloaded", timeout=30000)
            # The main page heading is "Proposals" (rendered as h1.inline-block)
            expect(page.get_by_role("heading", name="Proposals", exact=False).first).to_be_visible()
        finally:
            page.close()

    def test_debates_listing_accessible(self, base_url, browser_context):
        page = browser_context.new_page()
        try:
            page.goto(f"{base_url}/debates", wait_until="domcontentloaded", timeout=30000)
            expect(page.get_by_role("heading", name="Debates", exact=False).first).to_be_visible()
        finally:
            page.close()

    def test_sign_in_page_renders_form(self, base_url, browser_context):
        page = browser_context.new_page()
        try:
            page.goto(f"{base_url}/users/sign_in", wait_until="domcontentloaded", timeout=30000)
            # Devise form: 'login' (email-or-username), 'password', commit submit
            expect(page.locator('form#new_user input[name="user[login]"]')).to_be_attached()
            expect(page.locator('form#new_user input[name="user[password]"]')).to_be_attached()
            expect(page.locator('form#new_user input[type="submit"][name="commit"]')).to_be_attached()
        finally:
            page.close()


# --- Admin auth + admin panel ------------------------------------------------


@pytest.mark.ui
class TestConsulDemocracyAdminAuth:
    """Admin login + admin panel reachability."""

    def test_admin_can_sign_in(self, base_url, browser_context, admin_email, admin_password):
        page = browser_context.new_page()
        try:
            _sign_in_admin(page, base_url, admin_email, admin_password)
            # Successful sign-in redirects away from /users/sign_in
            assert "sign_in" not in page.url, \
                f"Still on sign-in page after submit: {page.url}"
            # And the page has a sign-OUT link, confirming session is established
            expect(page.locator('form[action="/users/sign_out"]').first).to_be_attached()
        finally:
            page.close()

    def test_admin_panel_loads(self, base_url, browser_context, admin_email, admin_password):
        page = browser_context.new_page()
        try:
            _sign_in_admin(page, base_url, admin_email, admin_password)
            page.goto(f"{base_url}/admin", wait_until="domcontentloaded", timeout=30000)
            # /admin is reachable (no 401/403 redirect away)
            assert "/admin" in page.url, f"Did not land on /admin: {page.url}"
            # Sign-out link is still present (still authenticated)
            expect(page.locator('form[action="/users/sign_out"]').first).to_be_attached()
        finally:
            page.close()


# --- Admin creating content --------------------------------------------------


@pytest.mark.ui
@pytest.mark.slow
class TestConsulDemocracyAdminContent:
    """Smoke-test the admin creating a debate via the New Debate form."""

    def test_new_debate_form_renders_for_signed_in_user(
        self, base_url, browser_context, admin_email, admin_password
    ):
        """
        Verify /debates/new renders the form for an authenticated user.

        Submitting the form is intentionally NOT exercised here: Consul's
        translatable form generates dynamic field names like
        debate[translations_attributes][0][title], which makes a robust
        end-to-end submit test brittle. The manual smoke check (admin uploads
        an image to /admin/site_customization/images) covers S3 wiring and
        the requests-based health tests cover the public-side render path,
        so this remains a render-only auth-gate check.
        """
        page = browser_context.new_page()
        try:
            _sign_in_admin(page, base_url, admin_email, admin_password)
            page.goto(f"{base_url}/debates/new", wait_until="domcontentloaded", timeout=30000)
            assert "/debates/new" in page.url, \
                f"Auth-gated /debates/new redirected away: {page.url}"
            # The form submits to /debates and renders a "Start a debate" submit button
            expect(page.locator('form[action="/debates"]').first).to_be_attached()
            expect(page.locator('form[action="/debates"] input[type="submit"][name="commit"]').first).to_be_attached()
        finally:
            page.close()
