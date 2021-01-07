

api-web-run:
	PULSE_HOME=`pwd` PYTHONPATH=`pwd` python weblistener.py --configfile config/listen_http.yaml

api-web-regen:
	PULSE_HOME=`pwd` PYTHONPATH=`pwd` routegen -e config/listen_http.yaml

api-sms-run:
	PULSE_HOME=`pwd` PYTHONPATH=`pwd` python smslistener.py --configfile config/listen_sms.yaml

api-sms-regen:
	PULSE_HOME=`pwd` routegen -e config/listen_sms.yaml > smslistener.py

console-sms-test:
	PULSE_HOME=`pwd` ./sms_console.py config/syntax_pulsesms.yaml 

qlisten-events:
	PULSE_HOME=`pwd` PYTHONPATH=`pwd` ./sqs-consume.py --config config/pulse_sqs.yaml --source pulse_events

qlisten-data:
	PULSE_HOME=`pwd` PYTHONPATH=`pwd` ./sqs-consume.py --config config/pulse_sqs.yaml --source pulse_data



