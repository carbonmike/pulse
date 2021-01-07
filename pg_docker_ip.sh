#!/bin/bash

CONTAINER_ID=`docker ps | grep pulse_db | awk '{ print $1 }'`
echo `docker inspect $CONTAINER_ID |jq -r .[0].NetworkSettings.Networks.pulse_default.IPAddress`
