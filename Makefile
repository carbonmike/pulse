

api-web-run:
	PULSE_HOME=`pwd` PYTHONPATH=`pwd` python weblistener.py --configfile config/pulse_web.yaml

api-sms-run:
	PULSE_HOME=`pwd` PYTHONPATH=`pwd` python smslistener.py --configfile config/listen_sms.yaml

api-sms-regen:
	PULSE_HOME=`pwd` routegen -e config/listen_sms.yaml > smslistener.py

qlisten-events:
	PULSE_HOME=`pwd` PYTHONPATH=`pwd` ./sqs-consume.py --config config/pulse_sqs.yaml --source pulse_events

qlisten-data:
	PULSE_HOME=`pwd` PYTHONPATH=`pwd` ./sqs-consume.py --config config/pulse_sqs.yaml --source pulse_data



