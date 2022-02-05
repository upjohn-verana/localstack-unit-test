# Glue testing

I used the glue example from [localstackpro examples](https://github.com/localstack/localstack-pro-samples/tree/master/glue-etl-jobs)

The just commands:

- `just localstack-up`
- `just glue-run-job`

The `run_job.sh` shell script sets up a glue database and a glue table.
It then runs the glue job in the `src` directory.  For whatever reason the glue job fails.
I tried to run it as a `pythonscript` and as `glueetl` and both failed.
