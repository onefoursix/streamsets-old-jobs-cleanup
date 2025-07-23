#!/usr/bin/env python3
#################################################################
# FILE:  get-old-jobs.py
#
# DESCRIPTION:    This script writes a list of INACTIVE Job instances that have not been run within a
#                 user-defined lookback period, for example, a week or a month. The list of old Job instances
#                 is written in JSON format to the local file system
#
# ARGS:           - last_run_threshold - The threshold date to mark Jobs as needing to be cleaned up
#
#                 - output_file - The full path for a file where the list of old jobs will be written to
#                                 The file must not already exist.
#
# USAGE:          $ python3 get-old-jobs.py <last_run_threshold> <output_file>
#
# USAGE EXAMPLE:  $ python3 get-old-jobs.py 2024-06-30 /Users/mark/old-jobs/old_jobs.json
#
# PREREQUISITES:
#
#  - Python 3.9+
#
# - StreamSets Platform SDK for Python v6.6+
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
#
#################################################################

import os,sys,json
from pathlib import Path
from datetime import date, datetime, timedelta
from streamsets.sdk import ControlHub


# Method to convert millis to datetime string
def millis_to_datetime_string(millis):
    seconds = millis / 1000.0
    dt = datetime.fromtimestamp(seconds)
    dt_string = dt.strftime('%Y-%m-%d %H:%M:%S')
    return dt_string

# Method that validates that the last_run_threshold command line parameter is a valid date and is at
# least one day behind the current date. Returns the last_run_threshold as millis or None if the parameter is not valid.
def validate_last_run_threshold_parameter(last_run_threshold_str):
    last_run_threshold = None
    try:
        last_run_threshold = datetime.strptime(last_run_threshold_str, "%Y-%m-%d")
    except ValueError:
        print("Error:  The last_run_threshold parameter \'{}\' is not a valid date in yyyy-mm-dd format".format(last_run_threshold_str))
        return None
    if not last_run_threshold.date() <= date.today() - timedelta(days=1):
        print(
            "Error: The last_run_threshold parameter \'{}\' is not at least one day earlier than the current date".format(
                last_run_threshold_str))
        return None
    if last_run_threshold is None:
        return None
    else:
        last_run_threshold_millis = int(last_run_threshold.timestamp() * 1000)
        return last_run_threshold_millis

# Method that validates that the output file does not exist. Returns True is the output file does not yet exist
# or False if the file already exists
def validate_output_file_parameter(output_file):
    file_path = Path(output_file)
    if not file_path.exists():
        return True
    else:
        return False


#####################################
# Main Program
#####################################

# A map of old Jobs. The key is the last run timestamp millis, the value is the Job
old_jobs = {}

# Get CRED_ID from the environment
CRED_ID = os.getenv('CRED_ID')

# Get CRED_TOKEN from the environment
CRED_TOKEN = os.getenv('CRED_TOKEN')

# Check the number of command line args
if len(sys.argv) != 3:
    print('Error: Wrong number of arguments')
    print('Usage: $ python3 get-old-jobs.py <last_run_threshold> <output_file>')
    print('Usage Example: $ python3 get-old-jobs.py 2024-06-30 /Users/mark/old-jobs/old_jobs.json')
    sys.exit(1)

# Validate the last_run_threshold parameter
last_run_threshold = sys.argv[1]
last_run_threshold_millis = validate_last_run_threshold_parameter(last_run_threshold)
if last_run_threshold_millis is None:
    sys.exit(1)
print("last_run_threshold: '{}'".format(last_run_threshold))
print("---------------------------------")

# Validate the output_file parameter
output_file = sys.argv[2]
if not validate_output_file_parameter(output_file):
    print("Error: Output file \'{}\' already exists".format(output_file))
    sys.exit(1)
print("Output file: '{}'".format(output_file))

# Connect to Control Hub
print("---------------------------------")
print('Connecting to Control Hub')
print("---------------------------------")
sch = ControlHub(credential_id=CRED_ID, token=CRED_TOKEN)

print('Writing old Job Instances to output file...')

# Loop through all Jobs
for job in sch.jobs:

    # Ignore Job Templates
    if not job.job_template:

        # Get the Job History
        history = job.history
        if history is not None and len(history) > 0:
            last_run = history[0]
            status = last_run.status

            # Only consider Jobs with status of INACTIVE
            if status == 'INACTIVE':

                # If the Job's last run is older than the threshold...
                if last_run.finish_time < last_run_threshold_millis:

                    # Add the job to the map
                    old_jobs[last_run.finish_time] = job

# Write the old Jobs to the output file in ascending datetime order (i.e. oldest first)
with open(output_file, 'w') as output_file:
    for last_run_millis in sorted(old_jobs.keys()):
        job = old_jobs[last_run_millis]
        last_run_finish_time = millis_to_datetime_string(last_run_millis)
        line = json.dumps({"Last Run": last_run_finish_time, "Job Name": job.job_name, "Job ID": job.job_id}) + '\n'
        output_file.write(line)
print("---------------------------------")
print('Done')