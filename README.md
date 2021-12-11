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
    python setup.py test



