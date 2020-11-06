# pulse
Open-source, SMS-aware microblogging system


Pulse is like Twitter, but open-source.

Users can interact with Pulse in one of two ways: Web or SMS. There is an HTTP API for web-based clients, and an SMS API which listens to SMS traffic
forwarded from Twilio (support for other VoIP providers TBA).  

## Getting Started

A live Pulse stack consists of:

- a web listener, started by the `make run-api-web` target
- an SMS listener, started by the `make run-api-sms` target
- a user-event queue consumer, started by the `make qlisten-events` target
- a data queue consumer, started by the `make qlisten-data` target

### Prerequisites

Install the dependencies by issuing `pipenv install`. `pipenv shell` will start the virtual environment.
This project also requires access to the following services:

- PostgreSQL v9.5 or greater
- S3 object storage
- two SQS queues configured on AWS: one for events, one for out-of-band event data


### Installing

[TODO: install instructions/runbook info]
