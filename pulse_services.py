#!/usr/bin/env python

import os
import sys
import time
import urllib
import json
from collections import namedtuple
from contextlib import contextmanager
from sqlalchemy import MetaData
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm.session import sessionmaker

import datetime

from snap import common
import redis
import requests
import boto3
import sqlalchemy as sqla
import uuid

from twilio.rest import Client


POSTGRESQL_SVC_PARAM_NAMES = [
    'host',
    'database',
    'schema',
    'username',
    'password'
]

PIPELINE_SVC_PARAM_NAMES = [
    'job_bucket_name',
    'posted_jobs_folder',
    'accepted_jobs_folder'
]

MONTH_INDEX = 0
DAY_INDEX = 1
YEAR_INDEX = 2


def parse_date(date_string):
    tokens = [int(token) for token in date_string.split("/")]
    return datetime.date(tokens[YEAR_INDEX],
                         tokens[MONTH_INDEX],
                         tokens[DAY_INDEX])



class CommandContext(object):
    def __init__(self, atrium_channel, **kwargs):
        pass

    def send(self, command_name, **kwargs):
        '''
        construct a message dictionary
        set the header so that Atrium will recognize the message as a command
        '''


class MessageContext(object):
    def __init__(self, atrium_channel, **kwargs):
        self.atrium_channel = atrium_channel


    def send(self, message_type, **kwargs):
        msg_dict = {
            "message_type": message_type,
            "body_data_type": "application/json",
            "timestamp": self.current_timestamp(),
            "sender_pid": os.getpid(),
            "body": kwargs
        }

        num_subscribers = self.redis_client.publish(self.atrium_channel, json.dumps(msg_dict))
        if num_subscribers:
            return True
        
        return False


class UserSession(object):
    def __init__(self):
        pass


class StreamContext(object):
    def __init__(self):
        pass



class AtriumClient(object):
    def __init__(self, **kwargs):
        self.atrium_channel = kwargs['atrium_channel']
        redis_params = {
            'host': kwargs['redis_host'],
            'port': kwargs['redis_port'],
            'db': kwargs['redis_db']
        }
        self.redis_client = redis.StrictRedis(**redis_params)

        self.user_sms_sessions = {}


    def current_timestamp(self):
        return datetime.datetime.now().isoformat()


    def create_session(self):
        return uuid.uuid4()


    def command_context(self, session: UserSession):
        # send a control signal (a command) to Atrium which will create (or look up)
        # a command queue: generate a globally-unique session ID and pass it to Atrium,
        # create a CommandSession object and pass the ID to it as a command channel
        # The newly-created CommandSession will send a command on the main Atrium channel
        # and (optionally) listen for the return on the command channel

        pass
        
    
    def lookup_username_by_mobile_number(self, user_sms_number: str, session, db_svc) -> str:
        
        User = db_svc.Base.classes.users
        query = session.query(User).filter(User.sms_phone_number == user_sms_number).filter(User.deleted_ts == None)
        record = query.one()
                    
        return record.username


    def message_context(self):
        # send a data signal (a message) to Atrium
        pass


    def connect_user_stream(self, userid, **kwargs):
        msg_dict = {
            "message_type": "test",
            "body_data_type": "text/plain",
            "timestamp": self.current_timestamp(),
            "sender_pid": os.getpid(),
            "body": f"connecting to user {userid}"
        }

        num_subscribers = self.redis_client.publish(self.atrium_channel, json.dumps(msg_dict))

    def create_topic_for_user_id(self, user_id: str):
        pass


    def get_topic_for_user_id(self, user_id: str):
        pass


    def open_user_session_sms(self, sms_number: str, user_id: str, **kwargs) -> UserSession:
        
        #db_service = kwargs.get('userdb')
        #db_service.lookup_user_account_sms(user_id, sms_number)

        session = UserSession()
        self.user_sms_sessions[sms_number] = session
        return session


    def get_user_session_sms(self, sms_number: str) -> UserSession:
        
        session = self.user_sms_sessions.get(sms_number)
        if not session:
            raise Exception(f'No user session for {sms_number}')
        
        #if self.session_is_expired(session):
        #    raise Exception(f'User session for {sms_number} is expired.')

        return session


    def close_session_sms(self, sms_number: str):
        
        session = self.find_user_session_sms(sms_number)
        if session:
            self.delete_user_session_sms(session)
        # if we can't find the session, do nothing
    

    def connect_user_stream(self, target_user_id: str, session: UserSession):
        
        stream_ctx = self.create_stream_context(session)
        
        # look up the topic for the target user ID
        topic = self.get_topic_for_user_id(target_user_id)

        # create a slot for a Kafka consumer assigned to that topic

        # send the request to atriumd

        # read result code and send status back to caller



class SMSService(object):
    def __init__(self, **kwargs):
        account_sid = kwargs['account_sid']
        auth_token = kwargs['auth_token']
        self.source_number = kwargs['source_mobile_number']

        if not account_sid:
            raise Exception('Missing Twilio account SID var.')

        if not auth_token:
            raise Exception('Missing Twilio auth token var.')

        self.client = Client(account_sid, auth_token)

    def send_sms(self, mobile_number, message):
        print('### sending message body via SMS from [%s] to [%s] :' % (self.source_number, mobile_number))
        print(message)

        message = self.client.messages.create(
            to='+1%s' % mobile_number,
            from_='+1%s' % self.source_number,
            body=message
        )

        return message.sid


class PostgreSQLService(object):
    def __init__(self, **kwargs):
        kwreader = common.KeywordArgReader(*POSTGRESQL_SVC_PARAM_NAMES)
        kwreader.read(**kwargs)

        self.db_name = kwargs['database']
        self.host = kwargs['host']
        self.port = int(kwargs.get('port', 5432))
        self.username = kwargs['username']
        self.password = kwargs['password']        
        self.schema = kwargs['schema']
        self.max_connect_retries = int(kwargs.get('max_connect_retries') or 3)
        self.metadata = None
        self.engine = None
        self.session_factory = None
        self.Base = None
        self.url = None

        url_template = '{db_type}://{user}:{passwd}@{host}/{database}'
        db_url = url_template.format(db_type='postgresql+psycopg2',
                                     user=self.username,
                                     passwd=self.password,
                                     host=self.host,
                                     port=self.port,
                                     database=self.db_name)

        retries = 0
        connected = False
        while not connected and retries < self.max_connect_retries:
            try:
                self.engine = sqla.create_engine(db_url, echo=False)
                self.metadata = MetaData(schema=self.schema)
                self.Base = automap_base(bind=self.engine, metadata=self.metadata)
                self.Base.prepare(self.engine, reflect=True)
                self.metadata.reflect(bind=self.engine)
                self.session_factory = sessionmaker(bind=self.engine, autoflush=False, autocommit=False)

                # this is required. See comment in SimpleRedshiftService 
                connection = self.engine.connect()                
                connection.close()
                connected = True
                print('### Connected to PostgreSQL DB.', file=sys.stderr)
                self.url = db_url

            except Exception as err:
                print(err, file=sys.stderr)
                print(err.__class__.__name__, file=sys.stderr)
                print(err.__dict__, file=sys.stderr)
                time.sleep(1)
                retries += 1

        if not connected:
            raise Exception('!!! Unable to connect to PostgreSQL db on host %s at port %s.' % 
                            (self.host, self.port))

    @contextmanager
    def txn_scope(self):
        session = self.session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    @contextmanager
    def connect(self):
        connection = self.engine.connect()
        try:
            yield connection
        finally:
            connection.close()


class S3Key(object):
    def __init__(self, bucket_name, s3_object_path):
        self.bucket = bucket_name
        self.folder_path = self.extract_folder_path(s3_object_path)
        self.object_name = self.extract_object_name(s3_object_path)
        self.full_name = s3_object_path

    def extract_folder_path(self, s3_key_string):
        if s3_key_string.find('/') == -1:
            return ''
        key_tokens = s3_key_string.split('/')
        return '/'.join(key_tokens[0:-1])

    def extract_object_name(self, s3_key_string):
        if s3_key_string.find('/') == -1:
            return s3_key_string
        return s3_key_string.split('/')[-1]

    def __str__(self):
        return self.full_name

    @property
    def uri(self):
        return os.path.join('s3://', self.bucket, self.full_name)


class S3Service(object):
    def __init__(self, **kwargs):
        kwreader = common.KeywordArgReader('local_temp_path', 'region')
        kwreader.read(**kwargs)

        self.local_tmp_path = kwreader.get_value('local_temp_path')
        self.region = kwreader.get_value('region')
        self.s3session = None
        self.aws_access_key_id = None
        self.aws_secret_access_key = None

        # we set this to True if we are initializing this object from inside
        # an AWS Lambda, because in that case we do not require the aws
        # credential parameters to be set. The default is False, which is what
        # we want when we are creating this object in a normal (non-AWS-Lambda)
        # execution context: clients must pass in credentials.

        should_authenticate_via_iam = kwargs.get('auth_via_iam', False)

        if not should_authenticate_via_iam:
            print("NOT authenticating via IAM. Setting credentials now.", file=sys.stderr)
            self.aws_access_key_id = kwargs.get('aws_key_id')
            self.aws_secret_access_key = kwargs.get('aws_secret_key')
            if not self.aws_secret_access_key or not self.aws_access_key_id:
                raise Exception('S3 authorization failed. Please check your credentials.')

            self.s3client = boto3.client('s3',
                                         aws_access_key_id=self.aws_access_key_id,
                                         aws_secret_access_key=self.aws_secret_access_key)
        else:
            self.s3client = boto3.client('s3', region_name=self.region)

    def upload_object(self, local_filename, bucket_name, bucket_path=None):
        s3_path = None
        with open(local_filename, 'rb') as data:
            base_filename = os.path.basename(local_filename)
            if bucket_path:
                s3_path = os.path.join(bucket_path, base_filename)
            else:
                s3_path = base_filename
            self.s3client.upload_fileobj(data, bucket_name, s3_path)
        return S3Key(bucket_name, s3_path)

    def upload_json(self, data_dict, bucket_name, bucket_path):
        binary_data = bytes(json.dumps(data_dict), 'utf-8')
        self.s3client.put_object(Body=binary_data, 
                                 Bucket=bucket_name, 
                                 Key=bucket_path)

    def upload_bytes(self, bytes_obj, bucket_name, bucket_path):
        s3_key = bucket_path
        self.s3client.put_object(Body=bytes_obj,
                                 Bucket=bucket_name,
                                 Key=s3_key)
        return s3_key

    def download_json(self, bucket_name, s3_key_string):
        obj = self.s3client.get_object(Bucket=bucket_name, Key=s3_key_string)
        return json.loads(obj['Body'].read().decode('utf-8'))


class APIError(Exception):
    def __init__(self, url, method, status_code):
        super().__init__(self,
                         'Error sending %s request to URL %s: status code %s' % (method, url, status_code))


APIEndpoint = namedtuple('APIEndpoint', 'host port path method')



class AtriumService(object):
    def __init__(self, **kwargs):
        self.user_sms_sessions = {}


    def is_expired(self, user_session) -> bool:
        return False


    def create_topic_for_user_id(self, user_id: str):
        pass


    def get_topic_for_user_id(self, user_id: str):
        pass


    def open_user_session_sms(self, sms_number: str, user_id: str, **kwargs) -> UserSession:
        
        #db_service = kwargs.get('userdb')
        #db_service.lookup_user_account_sms(user_id, sms_number)

        session = UserSession()
        self.user_sms_sessions[sms_number] = session
        return session


    def get_user_session_sms(self, sms_number: str) -> UserSession:
        
        session = self.user_sms_sessions.get(sms_number)
        if not session:
            raise Exception(f'No user session for {sms_number}')
        
        if self.session_is_expired(session):
            raise Exception(f'User session for {sms_number} is expired.')

        return session


    def close_session_sms(self, sms_number: str):
        
        session = self.find_user_session_sms(sms_number)
        if session:
            self.delete_user_session_sms(session)
        # if we can't find the session, do nothing
    

    def connect_user_stream(self, target_user_id: str, session: UserSession):
        
        stream_ctx = self.create_stream_context(session)
        
        # look up the topic for the target user ID
        topic = self.get_topic_for_user_id(target_user_id)

        # create a slot for a Kafka consumer assigned to that topic

        # send the request to atriumd

        # read result code and send status back to caller
