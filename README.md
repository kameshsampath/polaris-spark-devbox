# Spark Dev Box

## Build image

Fork and clone Clone the [Jupyter Docker Stacks](https://jupyter-docker-stacks.readthedocs.io/) repo 

```shell
gh repo clone https://github.com/jupyter/docker-stacks
cd docker-stacks
gh repo fork
```

## Build Spark Image

The following command builds the Spark3.5 with Hadoop3 image with Java 17

```
task build_spark_image
```

## Start the env

```shell
docker compose up -d minio nessie
```

Access the minio using <http://localhost:9000> and create a bucket named `warehouse`

### Start Spark 

```shell
docker compose up spark
```

Use the URL in the docker logs to connect to the server.