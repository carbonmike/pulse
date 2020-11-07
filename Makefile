

run-api-web:
	PULSE_HOME=`pwd` PYTHONPATH=`pwd` python weblistener.py --configfile config/pulse_web.yaml

run-api-sms:
	PULSE_HOME=`pwd` PYTHONPATH=`pwd` python smslistener.py --configfile config/pulse_sms.yaml

qlisten-events:
	PULSE_HOME=`pwd` PYTHONPATH=`pwd` ./sqs-consume.py --config config/pulse_sqs.yaml --source pulse_events

qlisten-data:
	PULSE_HOME=`pwd` PYTHONPATH=`pwd` ./sqs-consume.py --config config/pulse_sqs.yaml --source pulse_data



