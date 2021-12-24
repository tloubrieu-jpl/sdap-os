SDAP experiment with object storage

# Prerequisites

Set minio server (not used in the development yet)

Standalone minio:

Server install:

    brew install minio/stable/minio

Start the server

    export MINIO_ROOT_USER=myminio
    export MINIO_ROOT_PASSWORD=minio123AB

    minio server /Users/loubrieu/Documents/sdap/minio --address localhost:9000 --console-address localhost:19000

Client

    brew install minio/stable/mc
    mc --help

Create server alias:

    mc alias set minio http://localhost:9000 myminio minio123AB

Create a bucket:

    mc mb hls


## Copy test datasets

Create a bucket:

    mc mb hls


Copy some files:

    mc cp data/hls/s1_output_latlon_HLS_S30_T18TYN_2019263_cog.tif minio/hls
    mc cp data/hls/s1_output_latlon_HLS_S30_T18TYN_2019260_cog.tif minio/hls
    mc cp data/hls/s1_output_latlon_HLS_S30_T18TYN_2019253_cog.tif minio/hls


# Launch application and test

Set AWS credentials in environment (see https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-envvars.html)

    export AWS_ACCESS_KEY_ID={your key id}
    export AWS_SECRET_ACCESS_KEY={your secret}
    export AWS_DEFAULT_REGION={your region}


Install and run tests:

    pip install -e '.[dev]'
    python setup.py test &> out.log &

# Resource allocation

The resources needed to run the application can be estimated as follow:

- maximum size of 1 tile for each worker = T = 64 * x * y * t * obs dim, for example 64*3660*3660*1*6 = 5Gb
- maximum size of the user result returned to the user = R = 64*x*y*t*obs dims
- number of paralels workers: n


Total RAM = T*n + R

Number of CPU = n



