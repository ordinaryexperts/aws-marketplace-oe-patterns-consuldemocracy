# Integration Tests

Two test suites against a deployed pattern stack:

- `test_health.py` — requests-based smoke checks (HTTPS, `/elb-check`, branding, SSL cert, CFN stack state, EC2 instance running). 9 tests, ~5s.
- `test_workflows.py` — Playwright (headless Chromium) UI tests. Public homepage / listings / sign-in form, admin auth via Secrets Manager-fetched password, admin panel reachability, new-debate form auth gate. 7 tests, ~30s.

## Running against a deployed dev stack

The `devenv` Docker image doesn't ship with `pytest` or Playwright pre-installed. Install on the fly inside the container:

```bash
AWS_PROFILE=oe-patterns-dev docker compose run -w /code/test/integration --rm devenv bash -c "
  apt-get install -y -qq libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0 libdrm2 \
    libxkbcommon0 libatspi2.0-0 libxcomposite1 libxdamage1 libxfixes3 libxrandr2 \
    libgbm1 libasound2t64 > /dev/null 2>&1
  pip3 install -r requirements.txt --break-system-packages -q
  playwright install chromium >/dev/null 2>&1
  pytest -v
"
```

For just the requests-based health tests (no Playwright deps needed):

```bash
AWS_PROFILE=oe-patterns-dev docker compose run -w /code/test/integration --rm devenv bash -c "
  pip3 install -r requirements.txt --break-system-packages -q
  pytest test_health.py -v
"
```

## Configuration

Override target stack via env vars or CLI:

| Setting | Default (in `config.yaml`) | CLI override | Env override |
|---|---|---|---|
| Site URL | `https://consuldemocracy-dylan.dev.patterns.ordinaryexperts.com` | `--base-url=...` | `TEST_BASE_URL` |
| Stack name | `oe-patterns-consuldemocracy-dylan` | `--stack-name=...` | `TEST_STACK_NAME` |
| AWS region | `us-east-1` | — | `AWS_REGION` |

Skip Playwright/UI tests with `--skip-ui` (or just run `pytest test_health.py`).

## How admin login works in the Playwright suite

The `admin_password` fixture fetches the random password generated at AMI boot from Secrets Manager (`{stack_name}/instance/credentials`, key `admin_password`). The `admin_email` fixture reads the stack's `AdminEmailOutput`. The same suite runs unmodified against any stack name + region.
