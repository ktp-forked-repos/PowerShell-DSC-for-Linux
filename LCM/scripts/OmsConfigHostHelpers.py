#!/usr/bin/python
import json
import time
import datetime
import os
import math
import signal

def write_omsconfig_host_telemetry(message):
    omsagent_telemetry_path = '/var/opt/microsoft/omsconfig/status'
    dsc_host_telemetry_path = os.path.join(omsagent_telemetry_path, 'omsconfighost')

    if not os.path.exists(omsagent_telemetry_path):
        os.makedirs(omsagent_telemetry_path)

    if os.path.isfile(dsc_host_telemetry_path):
        with open(dsc_host_telemetry_path) as host_telemetry_file:
            try:
                host_telemetry_json = json.load(host_telemetry_file)
            except:
                host_telemetry_json = {}
                host_telemetry_json['operation'] = 'omsconfighost'
                host_telemetry_json['message'] = ''
                host_telemetry_json['success'] = 1
    else:
        os.mknod(dsc_host_telemetry_path)
        host_telemetry_json = {}
        host_telemetry_json['operation'] = 'omsconfighost'
        host_telemetry_json['message'] = ''
        host_telemetry_json['success'] = 1

    host_telemetry_json['message'] += message

    with open(dsc_host_telemetry_path, 'w+') as host_telemetry_file:
        json.dump(host_telemetry_json, host_telemetry_file)

def write_omsconfig_host_event(pathToCurrentScript, dsc_host_switch_exists):
    msg_template = '<OMSCONFIGLOG>[%s] [%d] [%s] [%d] [%s:%d] %s</OMSCONFIGLOG>'
    timestamp = datetime.datetime.fromtimestamp(time.time()).strftime('%Y/%m/%d %H:%M:%S')
    if dsc_host_switch_exists:
        msg_buffer = 'Using dsc_host'
    else:
        msg_buffer = 'Falling back to OMI'
    message = msg_template % (timestamp, os.getpid(), 'INFO', 0, pathToCurrentScript, 0, msg_buffer)
    write_omsconfig_host_telemetry(message)

def write_omsconfig_host_log(pathToCurrentScript, message, level = 'INFO'):
    log_entry_template = '[%s] [%d] [%s] [%d] [%s:%d] %s'
    timestamp = datetime.datetime.fromtimestamp(time.time()).strftime('%Y/%m/%d %H:%M:%S')
    log_entry = log_entry_template % (timestamp, os.getpid(), level, 0, pathToCurrentScript, 0, message)

    omsconfig_log_folder = '/var/opt/microsoft/omsconfig'
    if not os.path.exists(omsconfig_log_folder):
        os.makedirs(omsconfig_log_folder)

    print(log_entry)

    omsconfig_log_path = os.path.join(omsconfig_log_folder, 'omsconfig.log')
    with open(omsconfig_log_path, 'a+') as omsconfig_log_file:
        omsconfig_log_file.write(log_entry)

    omsconfig_detailed_log_path = os.path.join(omsconfig_log_folder, 'omsconfigdetailed.log')
    with open(omsconfig_detailed_log_path, 'a+') as omsconfig_detailed_log_file:
        omsconfig_detailed_log_file.write(log_entry)

def stop_old_host_instances():
    dsc_host_pid_path = '/opt/dsc/bin/dsc_host.pid'

    last_host_pid = 0

    if os.path.isfile(dsc_host_pid_path):
        with open(dsc_host_pid_path) as dsc_host_pid_file:
            try:
                last_host_pid = dsc_host_pid_file.read()
            except:
                pass
    
    if last_host_pid == 0:
        return
    
    # Timestamps are measured in seconds since epoch
    host_pid_last_modified_time = os.path.getmtime(dsc_host_pid_path)
    current_time = math.floor(time.time())
    timestamp_diff = current_time - host_pid_last_modified_time

    if (timestamp_diff < 0):
        return
    
    # If file was last modified more than 3 hours ago, we will kill the process
    if (timestamp_diff > 3600 * 3):
        try:
            os.kill(last_host_pid, signal.SIGTERM)
        except:
            pass
