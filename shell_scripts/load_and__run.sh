#!/bin/bash
image_tar=$1
image_name=$2
docker load -i $image_tar
docker run -d -p 5477:80 --name $image_name $image_name
