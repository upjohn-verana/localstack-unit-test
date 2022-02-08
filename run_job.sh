#!/bin/bash

BUCKET=glue-pyspark-test
JOB_NAME=test-job1
S3_URL=s3://$BUCKET/spark_job.py

echo Putting PySpark script to test S3 bucket ...
awslocal s3 mb s3://$BUCKET
awslocal s3 cp src/spark_job.py $S3_URL

echo Starting Glue job from PySpark script ...
awslocal glue create-job --name $JOB_NAME --role r1 \
  --command '{"Name": "glueetl", "ScriptLocation": "'$S3_URL'"}' \
  --connections '{"Connections": ["c1"]}'\
  --default-arguments '{"--additional-python-modules": "loguru==0.6.0"}'
run_id=$(awslocal glue start-job-run --job-name $JOB_NAME | jq -r .JobRunId)

state=$(awslocal glue get-job-run --job-name $JOB_NAME --run-id $run_id | jq -r .JobRun.JobRunState)
while [ "$state" != SUCCEEDED ]; do
  echo "Waiting for Glue job ID '$run_id' to finish (current status: $state) ..."
  sleep 4
  state=$(awslocal glue get-job-run --job-name $JOB_NAME --run-id $run_id | jq -r .JobRun.JobRunState)
done

echo "Done - Glue job execution finished. Please check the LocalStack container logs for more details."
