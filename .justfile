default:
    @just --list

localstack-up:
    docker compose -f ./docker/docker-compose-just-dynamo.yml up

localstack-down:
    docker compose -f ./docker/docker-compose-just-dynamo.yml down

glue-run-job:
    ./run_job.sh

create-deploy-bucket:
    awslocal s3 mb s3://vh-serverless-master-ue1

sls-deploy-local:
    SLS_DEBUG=* poetry run sls deploy --stage local --verbose

sls-invoke-local:
    SLS_DEBUG=* sls invoke local --function Basic --stage local

sls-step-function-invoke:
    SLS_DEBUG=* sls invoke stepf --name EpicPreProcessingStateMachine --stage local --data '{"ehr_connection_name": "epic", "delivery_date": "2021-09-01", "ingestion_id": "c25drn4idtlb8j6ojah0"}'

sls-first-time-local: create-deploy-bucket sls-deploy-local

stf-list-statemachines:
    awslocal stepfunctions list-state-machines

stf-list-executions arn:
    awslocal stepfunctions list-executions --state-machine-arn {{arn}}

stf-describe-execution arn:
    awslocal stepfunctions describe-execution --execution-arn {{arn}}

stf-execution-history arn:
    awslocal stepfunctions get-execution-history --execution-arn {{arn}}

