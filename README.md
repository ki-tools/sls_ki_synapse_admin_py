# SLS KI Synapse Admin

[![Build Status](https://travis-ci.com/pcstout/sls_ki_synapse_admin_py.svg?token=3ixgAsZG3yWFLjxfsY9Z&branch=master)](https://travis-ci.com/pcstout/sls_ki_synapse_admin_py)
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
  - `pipenv --three`
  - `pipenv shell`
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
  - Deploy to "development": `make deploy_development`
  - Deploy to "staging": `make deploy_staging`
  - Deploy to "production": `make deploy_production`
  
## Authentication

- Authentication will be done via Google OAuth.
- A whitelist of email addresses will be stored in an environment variable (in SSM) to restrict access to the site.


## Functionality

### Create Synapse Space (DCA)

This will create a new project in Synapse and configure it for ki contribution.

The steps are:

- Create a new Synapse project.
  - The format of the project name will be: `<INSTITUTION-SHORT-NAME>_<PRINCIPAL-INVESTIGATOR-NAME>`.
- Set the project's storage location to a specific (encrypted) S3 bucket.
- Create a new Synapse team and add it to the project.
  - The format of the team name will be: `KiContributor_<INSTITUTION-SHORT-NAME>_<PRINCIPAL-INVESTIGATOR-NAME>`.
- Invite user supplied email addresses to the team.
- Add a specific set of teams to the project.
- Create a specific set of folders in the project.
- Copy a wiki into the project from another Synapse project.
- Update a table with certain details about the project that was just created.

The contribution agreement table must have the following columns (at a minimum):

| Name | Type | Maximum Length | Description |
| :--- | :--- | :---           | :---        |
| Organization | `STRING` | 200 | The institution name provided by the user. |
| Contact | `STRING` | 200 | The first email address provided by the user. |
| Synapse_Project_ID | `ENTITYID` | | The ID of the Synapse project that was created. |
| Synapse_Team_ID | `INTEGER` | | The ID of the Synapse team that was created. |
| Agreement_Link | `LINK` | 1000 | URL to the contribution agreement document. |
| Start_Date | `DATE` | | The start date of the agreement. |
| End_Date | `DATE` | | The end date of the agreement. |
| Comments | `STRING` | 1000 | Any comments related to the agreement. |

### Grant Synapse Access Space (DAA)

This will create a new team in Synapse and share it with one or more projects and/or folders with download access.

The steps are:

- Create a new Synapse team.
  - The format of the team name will be: `<INSTITUTION-SHORT-NAME>_<DATA-COLLECTION-NAME>`.
- Invite user supplied email addresses to the team.
- Update a table with certain details about the team that was just created.

The contribution agreement table must have the following columns (at a minimum):

| Name | Type | Maximum Length | Description |
| :--- | :--- | :---           | :---        |
| Organization | `STRING` | 200 | The institution name provided by the user. |
| Contact | `STRING` | 200 | The first email address provided by the user. |
| Synapse_Team_ID | `INTEGER` | | The ID of the Synapse team that was created. |
| Granted_Entity_IDs |`STRING` | 1000 | The IDs of the Projects and/or Folders access was grated to. |
| Agreement_Link | `LINK` | 1000 | URL to the access agreement document. |
| Start_Date | `DATE` | | The start date of the agreement. |
| End_Date | `DATE` | | The end date of the agreement. |
| Comments | `STRING` | 1000 | Any comments related to the agreement. |

### Encrypt Synapse Space

This will set the storage location of a Synapse project to the value of `SYNAPSE_ENCRYPTED_STORAGE_LOCATION_ID`.
