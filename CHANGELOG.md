# Unreleased

# 2.0.0

* Upgrade Consul Democracy to 2.5.0 (from 2.2.0)
  * Ruby 3.2.4 → 3.3.11
  * Node.js 18 → 20
  * Rails 7.0 → 7.2
  * AI/LLM translation support added upstream (not enabled by default)
* Upgrade Ubuntu 22.04 → 24.04
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
