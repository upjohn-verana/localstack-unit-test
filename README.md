# Localstack Pro

This repo has a few branches to test different services in localstack.

need `awslocal` which is a wrapper on `aws-cli`.  Either install through pip or pipx:
`pipx install awscli-local` or `pip install awscli-local`

The repo makes use of `just`.  You can `brew install just` to get the recipes in the .justfile to work.
`just` basically works like `make`.

## Branches

master: basic lambda running from a stepfnuction
run_glue_in_container: glue job running in localstack docker container
run_lambda_test_of_calling_glue: run the glue job from a stepfunction

## Basic Usage

Start the docker container in one terminal:
`just localstack-up`

in a separate terminal deploy the serverless
`just sls-first-time-local`

run the stepfunction
`just sls-step-function-invoke`

you can use the other recipes to call the container to describe the stepfunction run
