#!/bin/bash
project_dir=$1
image_name=$2
docker build -t $image_name $project_dir
docker run -d -p 5477:80 --name $image_name $image_name
