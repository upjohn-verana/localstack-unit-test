# Glue testing

I used the glue example from [localstackpro examples](https://github.com/localstack/localstack-pro-samples/tree/master/glue-etl-jobs)

The just commands:

- `just localstack-up`
- `just glue-run-job`

The `run_job.sh` shell script runs the glue job in the `src` directory.

## Steps to run

- in one terminal start the docker container: `just localstack-up`
- in a separate terminal run: `just glue-run-job`

## Error and message from localstack support (2022-03-10)

The running of glue in the localstack docker container runs some commands to load libs.  The error
that comes up is an ssl error.  As localstack support said, when the docker container tries to "curl"
the libs the Verana vpn is blocking that call.  I did not reach out to Verana IT about the vpn.

### Notes from interaction with localstack support

We worked with localstack support to troubleshoot running a glue job in localstack pro.
The issue lies with Verana's vpn.  As the docker container sets up to run the glue job,
it "curl"s some essential files. Due to, what we believe, Verana's vpn the container hits an ssl error.

This is the command that returns the error
```
curl: (60) SSL certificate problem: unable to get local issuer certificate`
```
- enter the container: `docker exec -it localstack_main bash`

- run the curl command (this produces the ssl error):
```
curl -Lo /tmp/aws-glue-libs.zip https://github.com/awslabs/aws-glue-libs/archive/refs/heads/glue-1.0.zip
```

- The other command that should work:
```
curl -Lo /tmp/aws-glue-libs-java.zip https://localstack-web-assets.s3.amazonaws.com/aws-glue-libs.zip
```
