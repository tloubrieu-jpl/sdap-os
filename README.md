SDAP experiment with object storage and other technologies (ray.io, xarray...)

# Features

- Applies simple algorithms on earth observation datasets

- Read Cloud Optimized GeoTiff on S3 bucket
- Manage S3 bucket with public access or with access keys
- Manage datasets in any CRS (WGS84, UTM, ...)
- Manage multi-band datasets
- 

- Algorithms managed:
    - Spatial Mean: on a x,y,t range averages on x,y dimensions
    - EVI: linear combinations of multi-band spectra
    

# Prerequisites

- python 3.9
- datasets on s3


# Configure application and test

Set AWS credentials in environment (see https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-envvars.html)

    export AWS_ACCESS_KEY_ID={your key id}
    export AWS_SECRET_ACCESS_KEY={your secret}
    export AWS_DEFAULT_REGION={your region}


The collection configuration should follow the template found on `src/sdap/test/data_access/collection-config.yaml` 


Install and run tests:

    pip install -e '.[dev]'
    python setup.py test &> out.log &



# Run

Use command line 

        sdap --help

For example with `EVI` operator:

        sdap --conf ./src/sdap/test/data_access/collection-config.yaml \
             --collection hls \
             --x-range -71.24 -71.23 \
             --y-range 42.40 42.42 \
             --time-range 2017-01-01T00:00:00.000000+00:00 2017-06-01T00:00:00.000000+00:00 \
             --operator-name EVI \
             --operator-args '[[0,0,-2.5,2.5,0,0,0],[0,0,2.4,1,0,0,1]]' \
             --plot

With `SpatialMean` operator:

        sdap --conf ./src/sdap/test/data_access/collection-config.yaml \
             --secrets my_secrets.yaml \
             --collection hls \
             --bbox -71.24 42.40 -71.23 42.42 \
             --time-range 2017-01-01T00:00:00.000000+00:00 2017-06-01T00:00:00.000000+00:00 \
             --operator-name SpatialMean

        sdap --conf ./src/sdap/test/data_access/collection-config.yaml \
             --collection maiac \
             --bbox -71.25 42.39 -71.23 42.42 \
             --time-range 2019-01-01T00:00:00.000000+00:00 2019-02-01T00:00:00.000000+00:00 \
             --operator-name SpatialMean


             



# Resource allocation

The resources needed to run the application can be estimated as follow:

- maximum size of 1 tile for each worker = T = 64 * x * y * t * obs dim, for example 64*3660*3660*1*6 = 5Gb
- maximum size of the user result returned to the user = R = 64*x*y*t*obs dims
- number of paralels workers: n


Total RAM = T*n + R

Number of CPU = n



# Use with local minio

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
