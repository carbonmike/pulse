
containerid = `docker ps | grep atrium_svc_db | awk '{ print $$1 }'`
container_ipaddr = `./pg_docker_ip.sh`


show-dbdockerlog:
	docker logs $(containerid)

dockerlogin:
	docker exec -it $(containerid) bash

dblogin:
	psql -w -U postgres -h $(container_ipaddr) -p 5432

db-up:
	docker-compose -f atrium_svc/docker_pulsedb.yml up -d

db-down:
	docker-compose -f docker_pulsedb.yml down

db-bounce: db-down db-up

db-purge:
	psql -w -d postgres -U pulseuser -h $(container_ipaddr) -f sql/purge.sql

db-reset:
	psql -W -U postgres -h $(container_ipaddr) -f sql/db_ddl.sql

db-populate:	
	psql -w -U pulseuser -d pulse -h $(container_ipaddr) -f sql/core_ddl.sql

redis-up:
	docker-compose -f atrium_svc/docker_pulsedb.yml up -d redis

redis-down:
	docker-compose -f atrium_svc/docker_pulsedb.yml stop redis

api-web-run:
	PULSE_HOME=`pwd` PYTHONPATH=`pwd` python weblistener.py --configfile config/listen_http.yaml

api-web-regen:
	PULSE_HOME=`pwd` PYTHONPATH=`pwd` routegen -e config/listen_http.yaml

api-sms-run:
	PULSE_HOME=`pwd` PYTHONPATH=`pwd` python smslistener.py --configfile config/listen_sms.yaml

api-sms-regen:
	PULSE_HOME=`pwd` routegen -e config/listen_sms.yaml > smslistener.py

console-sms-test:	
	PULSE_HOME=`pwd` ./sms_console.py config/dialog_pulsesms.yaml --number $$PULSE_MOBILE_NUMBER

qlisten-events:
	PULSE_HOME=`pwd` PYTHONPATH=`pwd` ./sqs-consume.py --config config/pulse_sqs.yaml --source pulse_events

qlisten-data:
	PULSE_HOME=`pwd` PYTHONPATH=`pwd` ./sqs-consume.py --config config/pulse_sqs.yaml --source pulse_data


start-pulse: db-up



