import json
import os
import re
from datetime import date, datetime
from functools import partial
from pathlib import Path
from typing import Dict, List, Set
from uuid import uuid4

import boto3
from botocore.exceptions import ClientError
from helpers.logger import CwLogger
from helpers.secrets_manager import get_secret
from mypy_boto3_dynamodb import DynamoDBClient
from mypy_boto3_dynamodb.service_resource import Table
from psycopg2 import connect

logger = CwLogger(os.environ.get("LOG_THRESHOLD", "info"))
INGESTION_TRACKING_TABLE = os.environ["EPIC_INGEST_DYNAMODB_TABLE"]
INGESTION_BUCKET = os.environ.get("EPIC_SOURCE_BUCKET")


def get_dynamodb_resource(test_env: bool = False) -> DynamoDBClient:
    """Return the boto3 object for a dynamodb resource based for different environments

    Args:
        test_env (bool): if coming from a pytest call inside of docker-compose run then set to True

    Returns:
        DynamoDBClient: the boto3 object for a dynamodb resource
    """
    resource = boto3.resource("dynamodb")

    if test_env is True:
        return boto3.resource("dynamodb", endpoint_url="http://localstack:4566")

    if "LOCALSTACK_HOSTNAME" in os.environ:  # for running with serverless-local
        dynamodb_endpoint = f"http://{os.environ['LOCALSTACK_HOSTNAME']}:4566"
        resource = boto3.resource("dynamodb", endpoint_url=dynamodb_endpoint)
        return resource

    if os.environ["ENV"] == "local":  # running sls invoke locally
        return boto3.resource("dynamodb", endpoint_url="http://localhost:4566")

    return resource


def ingestion_table(dynamodb: DynamoDBClient) -> Table:
    """Return thet dynamodb table object"""
    return dynamodb.Table(INGESTION_TRACKING_TABLE)


def pull_date_from_file_name(filename: str) -> date:
    """Retrieve the date from a filename

    handles the cases:
        no separator
        `-` seperator
        `_` seperator

    Args:
        filename (str): filename with a date string in it

    Returns:
        date: the date object from the retrieved date string
    """
    date_part = re.match(r"^.*(\d\d\d\d)[-_]?(\d\d)[-_]?(\d\d).*$", filename)
    date_parsed = date(*[int(i) for i in date_part.groups()])

    return date_parsed


def get_home_di_connection() -> Dict:
    """
    Return the dsn config to be used in a psycopg2 connection
    """
    config = get_secret(os.environ["db_secret"], "us-east-1")
    dsn_dict = dict(
        host=config["host"], database=config["database"], user=config["username"], password=config["password"]
    )
    return dsn_dict


def retrieve_expected_file_count(ingestion_id: str) -> int:
    """From home_di pull the config for expected file count for an ingestion id

    Args:
        ingestion_id (str): the ingestion_id for the desired config

    Returns:
        int: the integer value of the expected file count
    """
    query = """SELECT tags
                FROM public.deployment
                WHERE vh_deployment_id = %(deployment_id)s;
            """

    home_di_dsn = get_home_di_connection()
    with connect(**home_di_dsn) as home_di:
        with home_di.cursor() as cursor_:
            cursor_.execute(query, {"deployment_id": ingestion_id})
            tags = cursor_.fetchone()
    try:
        expected_file_count = tags[0]["expected_file_count"]

    except TypeError:
        raise Exception(
            "Error with retrieving the ingestion_id from home_di."
            f" The ingestion_id {ingestion_id} may not be in the 'deployment' table"
            " or the 'tags' field does not have 'expected_file_count' as a key."
        )
    except KeyError:
        raise Exception(
            "Error with retrieving the 'expected_file_count' from home_di."
            f" The 'tags' field for the ingestion_id {ingestion_id}"
            " does not have 'expected_file_count' as a key."
        )
    else:
        logger.info(f"Expected file count: {expected_file_count}")

    return expected_file_count


def retrieve_extract_id(ingestion_id: str, delivery_date: date, dynamodb: DynamoDBClient) -> str:
    delivery_date_db_format = delivery_date.isoformat()
    table = ingestion_table(dynamodb)
    record = table.get_item(
        TableName=INGESTION_TRACKING_TABLE,
        Key={"ingestion_id": ingestion_id, "delivery_date": delivery_date_db_format},
        AttributesToGet=[
            "extract_id",
        ],
    )
    extract_id = record["Item"]["extract_id"]
    logger.info(
        "Array of extract id retrieved",
        meta_dict=dict(extract_id=extract_id, ingestion_id=ingestion_id, delivery_date=delivery_date_db_format),
    )
    return extract_id


def retrieve_extract_file_array(ingestion_id: str, delivery_date: date, dynamodb: DynamoDBClient) -> Set:
    delivery_date_db_format = delivery_date.isoformat()
    table = ingestion_table(dynamodb)
    record = table.get_item(
        TableName=INGESTION_TRACKING_TABLE,
        Key={"ingestion_id": ingestion_id, "delivery_date": delivery_date_db_format},
        AttributesToGet=[
            "extract_files_received",
        ],
    )
    extract_files_received = record["Item"]["extract_files_received"]
    logger.info(
        "Array of extract files retrieved",
        meta_dict=dict(
            array_of_files=extract_files_received, ingestion_id=ingestion_id, delivery_date=delivery_date_db_format
        ),
    )
    return extract_files_received


def retrieve_extract_file_count(ingestion_id: str, delivery_date: date, dynamodb: DynamoDBClient) -> int:
    """Pull the count of files tracked for an extract

    Args:
        ingestion_id (str): ingestion_id
        delivery_date (date): delivery_date
        dynamodb (DynamoDBClient): boto3 object dynamodb resource

    Returns:
        int: count of files tracked for the extract
    """
    extract_files_received = retrieve_extract_file_array(ingestion_id, delivery_date, dynamodb)
    received_files_count = len(extract_files_received)
    logger.info(
        "Count of files recorded is retrieved",
        meta_dict=dict(
            ingestion=ingestion_id, delivery_date=delivery_date.isoformat(), received_files_count=received_files_count
        ),
    )

    return received_files_count


def update_extract_received_complete(ingestion_id: str, delivery_date: date, dynamodb: DynamoDBClient) -> None:
    """
    Set the attribute for an extract to the present time for tracking all files received

    Args:
        ingestion_id (str): ingestion_id
        delivery_date (date): delivery_date
        dynamodb (DynamoDBClient): boto3 object dynamodb resource

    Returns:
        None:
    """
    logger.info(
        "Update dynamodb table with extract received date for this extract",
        meta_dict=dict(ingestion_id=ingestion_id, delivery_date=delivery_date),
    )
    delivery_date_db_format = delivery_date.isoformat()

    extract_files_complete_attribute = "extract_files_received_complete_date"

    table: Table = ingestion_table(dynamodb)

    try:
        _ = table.update_item(
            Key={
                "ingestion_id": ingestion_id,
                "delivery_date": delivery_date_db_format,
            },
            UpdateExpression=f"SET {extract_files_complete_attribute} = :extract_files_received_complete_date",
            ConditionExpression="attribute_not_exists(extract_files_received_complete_date)",
            ExpressionAttributeValues={
                ":extract_files_received_complete_date": datetime.utcnow().isoformat(),
            },
            ReturnValues="UPDATED_NEW",
        )
    except ClientError as e:
        if e.response["Error"]["Code"] != "ConditionalCheckFailedException":
            # for errors that are not caused by the conditional check then re-raise exception
            raise
        logger.info(
            f"The attribute {extract_files_complete_attribute} is already set"
            f" for the ingestion_id = {ingestion_id} and delivery_date = {delivery_date}."
            f" The update if the {extract_files_complete_attribute}"
        )
    else:
        logger.info(f"The attribute, {extract_files_complete_attribute}, has been added now that all files received")


def add_extract_file(ingestion_id: str, delivery_date: date, extract_file: str, dynamodb: DynamoDBClient) -> None:
    """Add a file to an extract

    In the case of a new extract (not in the table yet), then set up the extract_id anad extract start date
        along with storing the filename
    For the case of an existing extract then just add the filename

    Args:
        ingestion_id (str): ingestion_id
        delivery_date (date): delivery_date
        extract_file (str): extract_file
        dynamodb (DynamoDBClient): boto3 object dynamodb resource

    Returns:
        None:
    """

    delivery_date_db_format = delivery_date.isoformat()

    table: Table = ingestion_table(dynamodb)

    try:
        extract_id_created = str(uuid4())
        _ = table.put_item(
            Item={
                "ingestion_id": ingestion_id,
                "delivery_date": delivery_date_db_format,
                "extract_files_received": {extract_file},
                "extract_id": extract_id_created,
                "extract_files_received_start_date": datetime.utcnow().isoformat(),
            },
            ConditionExpression="ingestion_id <> :ingestion_id and delivery_date <> :delivery_date",
            ExpressionAttributeValues={":ingestion_id": ingestion_id, ":delivery_date": delivery_date_db_format},
        )
        logger.info(
            f"The file has been added to the tracking table with the extract_id: {extract_id_created}",
            meta_dict={"extract_id": extract_id_created, "ingestion_id": ingestion_id, "extract_file": extract_file},
        )

    except ClientError as e:
        if e.response["Error"]["Code"] != "ConditionalCheckFailedException":
            # for errors that are not caused by the conditional check then re-raise exception
            raise

        record = table.update_item(
            Key={
                "ingestion_id": ingestion_id,
                "delivery_date": delivery_date_db_format,
            },
            UpdateExpression="ADD extract_files_received :extract_file",
            ExpressionAttributeValues={
                ":extract_file": {extract_file},
            },
            ReturnValues="ALL_NEW",
        )
        logger.info(
            "The file has been added to the exisitng record", meta_dict=dict(record_udpate=record, s3_key=extract_file)
        )


def copy_file_to_extract_id(s3_file_key: str, extract_id: str) -> Dict:
    source_bucket = INGESTION_BUCKET
    destination_bucket = source_bucket

    path_parts_s3_key = Path(s3_file_key).parts

    source_file_key = "/".join(path_parts_s3_key[2:])

    ehr_connection_name = path_parts_s3_key[2]  # such as `epic`
    ingestion_id = path_parts_s3_key[3]
    file_name = path_parts_s3_key[-1]

    destination_path = f"{ehr_connection_name}/{ingestion_id}/{extract_id}/{file_name}"

    logger.info("Copy individual file", meta_dict=dict(file_name=file_name, destination_path=destination_path))

    s3 = boto3.client("s3")
    copy_response = s3.copy(
        CopySource={"Bucket": source_bucket, "Key": source_file_key},
        Bucket=destination_bucket,
        Key=destination_path,
    )

    _ = s3.delete_object(
        Bucket=source_bucket,
        Key=source_file_key,
    )
    return copy_response


def copy_files_stored_in_array(ingestion_id: str, delivery_date: date) -> List:
    dynamodb = get_dynamodb_resource()
    files_to_copy = retrieve_extract_file_array(ingestion_id, delivery_date, dynamodb)
    logger.info("Retrieved files to copy", meta_dict=dict(files=files_to_copy))

    extract_id = retrieve_extract_id(ingestion_id, delivery_date, dynamodb)
    logger.info("Retrieved extract id", meta_dict=dict(extract_id=extract_id))

    copy_file = partial(copy_file_to_extract_id, extract_id=extract_id)
    result_copied_files = [copy_file(i) for i in files_to_copy]
    logger.info("Files copied", meta_dict=dict(response_copied_files=result_copied_files))
    return result_copied_files


def trigger_step_function(ehr_connection_name: str, ingestion_id: str, delivery_date: date) -> Dict:
    delivery_date_iso_format = delivery_date.isoformat()

    logger.info(
        "Trigger step function",
        meta_dict=dict(
            ehr_connection_name=ehr_connection_name, ingestion_id=ingestion_id, delivery_date=delivery_date_iso_format
        ),
    )

    sfn = boto3.client("stepfunctions")
    if os.environ["ENV"] == "local":  # running sls invoke locally
        sfn = boto3.client("stepfunctions", endpoint_url="http://localhost:4566")

    sfn_arn = os.environ["SFN_ARN"]

    sfn_input = dict(
        ehr_connection_name=ehr_connection_name, ingestion_id=ingestion_id, delivery_date=delivery_date_iso_format
    )
    response = sfn.start_execution(stateMachineArn=sfn_arn, input=json.dumps(sfn_input))

    return {"statusCode": 200, "body": "Success", "response": str(response)}
