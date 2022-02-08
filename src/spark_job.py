from loguru import logger


def main():
    logger.info("what")
    print("start")
    print("this is a whol bunch of things")
    redshift_temp_dir = "s3://glue-sample-target/temp-dir/"

    return {"bam": redshift_temp_dir}


if __name__ == "__main__":
    main()
