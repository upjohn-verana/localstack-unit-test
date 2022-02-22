import boto3
from loguru import logger

s3 = boto3.client("s3")


def main():
    logger.info("what")
    print("start")
    print("this is a whol bunch of things")
    redshift_temp_dir = "s3://glue-sample-target/temp-dir/"

    s3.put_object(
        Bucket="glue-pyspark-test",
        Key="chad_thing.txt",
        Body=b"stuff",
    )

    return {"bam": redshift_temp_dir}


if __name__ == "__main__":
    main()
