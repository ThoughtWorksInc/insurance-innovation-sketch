## Introduction

This project provides a skeleton for various product integrations. That approach provides:
* Reduced application code overhead
* Increased security
* Continous introduction of new infrastructure features
* Lower operational costs

## Required software

You'll need to download and install the following software:

* [Python 3.6](https://www.python.org/downloads/)
* [Pipenv](https://pypi.org/project/pipenv/)
* [AWS CLI](https://aws.amazon.com/cli/)
* [AWS SAM CLI](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-install.html)

Make sure you have set up AWS credentials (typically placed under `~/.aws/credentials` or `~/.aws/config`). The credentials you're using should have "enough" privileges to provision all required services. You'll know the exact definition of "enough" when you get "permission denied" errors :)

Now, indicate which AWS profile should be used by the provided scripts, e.g,:

```bash
export AWS_PROFILE=[your-aws-profile]
```

## Python environment

Create the Python virtual environment and install the dependencies:

```bash
# from the project's root directory
pipenv --python 3.6 # creates Python 3.6 virtual environment
pipenv shell    # activate the virtual environment
pipenv install  # install dependencies
```

To know where the virtual environments and the dependencies are installed type this:

```bash
pipenv --venv
```

## Deploying the Solution

### Deploying the API

```bash
# from the project's root directory
./deploy_scripts/package_api.sh config-dev && ./deploy_scripts/deploy_api.sh config-dev
```

## Observability

We enabled observability of this application via [AWS X-Ray](https://aws.amazon.com/xray/).