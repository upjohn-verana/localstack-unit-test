import time

import boto3
from botocore.exceptions import ClientError
from loguru import logger

glue_job = "test-job1"
glue_job_file = "spark_job.py"
bucket = "glue-pyspark-test"
job_s3 = f"s3://{bucket}/{glue_job_file}"


def get_glue_client():
    glue = boto3.client(
        "glue",
        endpoint_url="http://localhost:4566",
        use_ssl=False,
    )
    return glue


def create_glue_job():
    third_party_packages = ",".join(["loguru==0.6.0"])
    glue = get_glue_client()
    try:
        glue.create_job(
            Name=glue_job,
            Role="r1",
            Command={
                "Name": "glueetl",
                "ScriptLocation": job_s3,
                "PythonVersion": "3",
            },
            DefaultArguments={
                # "--TempDir": "s3://lf-poc-vh-raw/glue_job/temp/",
                "--enable-continuous-cloudwatch-log": "true",
                "--enable-continuous-log-filter": "false",
                "--enable-metrics": "",
                "--job-bookmark-option": "job-bookmark-disable",
                "--job-language": "python",
                "--additional-python-modules": third_party_packages,
            },
            MaxRetries=0,
            Timeout=2880,
            GlueVersion="3.0",
            WorkerType="Standard",
            NumberOfWorkers=1,
        )

    except ClientError as error:
        if error.response["Error"]["Code"] == "IdempotentParameterMismatchException":
            logger.info(f"Glue job already exists: {glue_job}")
        else:
            raise
    logger.info("done glue create")


def run_glue_job():
    glue = get_glue_client()
    result = glue.start_job_run(
        JobName=glue_job,
        # Arguments={
        #     "--vh_deployment_id": "c1d5so4idtlf4cam0l4g",
        #     "--vh_pull_id": "c7aes4uv0000qa4oj9vg",
        #     "--s3_uri": "s3://vh-master-ue1-dev-data-lake/raw/ra_data/c1d5so4idtlf4cam0l4g/c7aes4uv0000qa4oj9vg",
        #     # "--vh_pull_id": "temper",
        #     # "--s3_uri": "s3://vh-master-ue1-dev-data-lake/raw/ra_data/c1d5so4idtlf4cam0l4g/temper",
        #     "--s3_bucket": "vh-master-ue1-dev-data-lake",
        # },
    )

    # status = glue.get_job_run(JobName=glue_job, RunId=result["JobRunId"])
    # while status["JobRun"]["JobRunState"] == "RUNNING":
    #     logger.info("still running")
    #     time.sleep(10)
    #     status = glue.get_job_run(JobName=glue_job, RunId=result["JobRunId"])

    # logger.info(f"Job: {status['JobRun']['JobRunState']}")
    logger.info(result)
    # logger.info("Done")


if __name__ == "__main__":
    create_glue_job()
    run_glue_job()
    logger.info("done")
