# Unreleased

# 2.0.1

* Upgrade Consul Democracy to 2.5.1 (from 2.5.0) - dependency-only patch release (gem/npm bumps), no Ruby/Node/Rails version changes
* Upgrade aws-marketplace-utilities packer scripts to 1.10.3 (from 1.10.0) - picks up an EFS-utils build reliability fix (cmake/golang-go/rustup toolchain)
* Introduce versioned AMI parameter `AsgAmiIdv201` (from `AsgAmiIdv200`)
* Fix `Dockerfile` missing `test/integration/requirements.txt` install - `make test-integration` had no pytest available
* Fix `docker-compose.yml` not passing `TEST_BASE_URL`/`TEST_STACK_NAME` through to the container, so integration test overrides were silently ignored

# 2.0.0

* Upgrade Consul Democracy to 2.5.0 (from 2.2.0)
  * Ruby 3.2.4 to 3.3.11
  * Node.js 18 to 20
  * Rails 7.0 to 7.2
  * AI/LLM translation support added upstream (not enabled by default)
* Upgrade Ubuntu 22.04 to 24.04
* Upgrade OE Common Constructs to 4.5.1 (from 3.20.0)
  * Upgrade Aurora PostgreSQL to 15.13 (was 15.4) *causes downtime during upgrade*
* Upgrade aws-cdk-lib to 2.225.0 (from 2.120.0)
* Upgrade OE devenv to 2.8.3 (from 2.5.3)
* Migrate to AWS Marketplace Catalog API submission (replaces PLF spreadsheet)
* Rebrand to "Consul Democracy on AWS by FOSSonCloud"
* Introduce versioned AMI parameter (`AsgAmiIdv200`)
* Add taskcat regression tests and pytest integration test scaffold
* Fix `consul/installer` clone URL to canonical `consuldemocracy/installer`

# 1.0.1

* Adding link to product

# 1.0.0

* Initial development
