
#!/usr/bin/env python

 
from snap import snap
from snap import core
import json
from snap.loggers import transform_logger as log



def ping_func(input_data, service_objects, **kwargs):
    raise snap.TransformNotImplementedException('ping_func')

def system_status_func(input_data, service_objects, **kwargs):
    raise snap.TransformNotImplementedException('system_status_func')

def sms_responder_func(input_data, service_objects, **kwargs):
    raise snap.TransformNotImplementedException('sms_responder_func')
