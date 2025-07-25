#!/usr/bin/env python3
#################################################################
# FILE:  delete-old-jobs.py
#
# DESCRIPTION:    This script attempts to delete Jobs instances listed in the input file.
#                 Job Instances and Job Template Instances will be deleted, unless there
#                 are permission issues, or in cases where Job instances are referenced by
#                 Sequences or Topologies.
#
# ARGS:           - input_file - A JSON list of Job instances to delete.
#
# USAGE:          $ python3 delete-old-jobs.py <input_file>
#
# USAGE EXAMPLE:  $ python3 delete-old-jobs.py /Users/mark/old-jobs/old_jobs.json
#
# PREREQUISITES:
#
#  - Python 3.9+
#
# - StreamSets Platform SDK for Python v6.0+
#   See: https://docs.streamsets.com/platform-sdk/latest/welcome/installation.html
#
# - StreamSets Platform API Credentials for a user with Organization Administrator role
#
# - Before running the script, export the environment variables CRED_ID and CRED_TOKEN
#  with the StreamSets Platform API Credentials, like this:
#
#    $ export CRED_ID="40af8..."
#    $ export CRED_TOKEN="eyJ0..."
#
#################################################################

import os,sys, json
from pathlib import Path
from datetime import datetime
from streamsets.sdk import ControlHub

# Method to convert a datetime string of the form 'yyy-dd-mm' to millis
def convert_dt_string_to_millis(dt_string):
    dt = datetime.strptime(dt_string, "%Y-%m-%d")
    return int(dt.timestamp() * 1000)

# Method to convert millis to a datetime string
def convert_millis_to_dt_string(millis):
    dt = datetime.fromtimestamp(millis / 1000)
    return dt.strftime("%Y-%m-%d %H:%M:%S")

# Method that validates the input_file command line parameter.
# Returns True if the input_file exists and is readable or False otherwise
def validate_input_file_parameter(the_input_file):
    file_path = Path(the_input_file)
    if file_path.is_file() and os.access(file_path, os.R_OK):
        return True
    else:
        print(f"Error: Input File \'{input_file}\' either does not exist or is not readable")
        return False

# Method to confirm the Job has not been run since it was flagged as old
# Returns True if the last Job run is before the last_run_threshold
def job_has_not_been_run_recently(job, the_last_run_threshold):
    last_run_threshold_millis = convert_dt_string_to_millis(the_last_run_threshold)
    try:
        history = job.history
        if history is not None and len(history) > 0:
            last_run = history[0]
            last_run_millis = last_run.finish_time
            if last_run_millis < last_run_threshold_millis:
                return True
            else:
                last_run_dt = convert_millis_to_dt_string(last_run_millis)
                print(f"- Job was run at \'{last_run_dt}\' which is more recent than the last_run_threshold of \'{the_last_run_threshold}\'")
                print(" --> Job will not be deleted.")
    except Exception as ex:
        print(f"- Error confirming Job has not been run recently \'{job.job_name}\': \'{ex}\'")
        print(" --> Job will not be deleted.")
    return False

# Method to confirm the Job has INACTIVE status. Return True or False
def job_is_inactive(the_job):
    try:
        history = the_job.history
        if history is not None and len(history) > 0:
            last_run = history[0]
            status = last_run.status
            if status == 'INACTIVE':
                return True
            else:
                print(f"Error: Job \'{the_job.job_name}\' has status \'{status}\'; the Job should have status of \'INACTIVE\' to be deleted")
    except Exception as ex:
        print(f"Error getting status for Job \'{the_job.job_name}\': \'{ex}\'")
    return False

# Method to get a Job from SCH using the job_id. Returns the Job or None if the
# Job is not found or if there is any issue
def get_job(the_job_info):
    job_id = the_job_info["job_id"]
    job_name = the_job_info["job_name"]

    try:
        query = 'id=="' + job_id + '"'
        jobs = sch.jobs.get_all(search=query)
        if jobs is None or len(jobs) == 0:
            print(f"Error getting Job from Control Hub \'{job_name}\': Job not found")
        else:
            job = jobs[0]
            return job
    except Exception as ex:
        print(f"Error getting Job from Control Hub \'{job_name}\': {ex}")
    return None

# Method to delete a Job. The deletion attempt might fail due to permission issues
# or if the Job is referenced by a Topology, a Task, or a Schedule
def delete_job(job):
    try:
        sch.delete_job(job)
        print(f"- Job was deleted.")
    except Exception as ex:
        print(f"Error: Attempt to delete Job failed; {ex}")

# Method to handle each line the input file
def handle_line(the_job_info):

    print(f"Preparing to delete Job \'{job_info['job_name']}\' with Job ID \'{job_info['job_id']}\'")

    # Get the Job
    job = get_job(the_job_info)
    if job is not None:

        print("- Found Job")

        # Make sure the Job is INACTIVE
        if job_is_inactive(job):
            print("- Job has status \'INACTIVE\'")

            # Make sure the Job hasn't been run since it was identified as old
            if job_has_not_been_run_recently(job, job_info['last_run_threshold']):

                # Try to delete the Job
                delete_job(job)
                
    print("---------------------------------")

#####################################
# Main Program
#####################################

# Get CRED_ID from the environment
CRED_ID = os.getenv('CRED_ID')

# Get CRED_TOKEN from the environment
CRED_TOKEN = os.getenv('CRED_TOKEN')

# Check the number of command line args
if len(sys.argv) != 2:
    print('Error: Wrong number of arguments')
    print('Usage: $ python3 delete-jobs.py <input_file>')
    print('Usage Example: $ python3 delete-jobs.py /Users/mark/old-jobs/old_jobs.json')
    sys.exit(1)

# Validate the input_file parameter
input_file = sys.argv[1]
print("---------------------------------")
print(f"input_file: '{input_file}'")
if not validate_input_file_parameter(input_file):
    sys.exit(1)

# Connect to Control Hub
print("---------------------------------")
print('Connecting to Control Hub')
sch = ControlHub(credential_id=CRED_ID, token=CRED_TOKEN)

# Process each line of the input_file
with open(input_file, 'r') as f:
    for line in f:
        try:
            job_info = json.loads(line)
            handle_line(job_info)
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON for line {line}: {e}")

print('Done')
