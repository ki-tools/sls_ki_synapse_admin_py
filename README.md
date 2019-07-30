# SLS KI Synapse Admin

[![Build Status](TBD)](TBD)
[![Coverage Status](TBD)](TBD)

## Overview

A [Serverless](https://serverless.com/framework/docs/getting-started) application that runs on [AWS Lambda](https://aws.amazon.com/lambda) serving a web interface via [Flask](https://github.com/pallets/flask) for maintaining projects in [Synapse](https://www.synapse.org).

## Development Setup

- [Install the Serverless Framework](https://serverless.com/framework/docs/providers/aws/guide/quick-start)
  - `npm install -g serverless`
  - Configure your AWS credentials by following [these directions](https://serverless.com/framework/docs/providers/aws/guide/credentials)
- Install Serverless Plugins:
  - `npm install`
- Create and activate a Virtual Environment:
  - `python3 -m venv .venv`
  - `source .venv/bin/activate`
- Configure environment variables:
  - Copy each file in [templates](templates) into the project's root directory and edit each file to contain the correct values.
- Install Python Dependencies:
  - `make reqs`
- Run tests.
  - `make test`

## Deploying

- Populate SSM with the environment variables. This only needs to be done once or when the files/values change.
  - `./scripts/set_ssm.py --stage <service-stage>` 
    - Example: `./scripts/set_ssm.py --stage production`
- Create the `A` records in Route53 if using a custom domain. This only needs to be done once for each stage.
  - `sls create_domain --stage <stage>`
    - Example: - `sls create_domain --stage production` 
  - See [serverless-domain-manager](https://github.com/amplify-education/serverless-domain-manager) for more details on configuring your custom domain.
- Deploy to AWS
  - Deploy to "dev": `make deploy_dev`
  - Deploy to "staging": `make deploy_staging`
  - Deploy to "production": `make deploy_production`
  
## Authentication

- TBD...

## Manual Testing

- View Logs: `sls logs -f graphql --tail`
- TBD...
