#!/bin/bash

CONTAINER_ID=`docker ps | grep atrium_svc_db | awk '{ print $1 }'`
echo `docker inspect $CONTAINER_ID |jq -r .[0].NetworkSettings.Networks.atrium_svc_default.IPAddress`
