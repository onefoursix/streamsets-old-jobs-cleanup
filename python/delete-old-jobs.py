#!/usr/bin/env python3
#################################################################
# FILE:  delete-old-jobs.py
#
# DESCRIPTION:    This script deletes all Jobs instances listed in the input file.
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
from streamsets.sdk import ControlHub

# Method that validates the input_file command line parameter.
# Returns True if the input_file exists and is readable or False otherwise
def validate_input_file_parameter(input_file):
    file_path = Path(input_file)
    if file_path.is_file() and os.access(file_path, os.R_OK):
        return True
    else:
        print(f"Error: Input File \'{input_file}\' either does not exist or is not readable")
        return False

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

print("---------------------------------")
print('Deleting Jobs...')
print("---------------------------------")

# Process each line of the input_file
with open(input_file, 'r') as f:
    for line in f:
        try:
            obj = json.loads(line)
            job_id = obj["Job ID"]

            try:
                # Get the Job from Control Hub using its ID
                query = 'id=="' + job_id + '"'
                jobs = sch.jobs.get_all(search=query)

                # Handle if Job is not found
                if jobs is None or len(jobs) == 0:
                    print(f"Error exporting Job \'{obj["Job Name"]}\' with job ID \'{job_id}\': Job not found")

               # Export Job
                else:
                    job = jobs[0]

                    # replace '/' with '_' in Job name
                    job_name = job.job_name.replace("/", "_")
                    export_file_name = export_dir + '/' + job_name + '.zip'

                    print(f"Exporting Job \'{job.job_name}\' into the file \'{export_file_name}\'")


                    data = sch.export_jobs([job])

                    # Export a zip file for the Job
                    with open(export_file_name, 'wb') as file:
                        file.write(data)

            except Exception as e:
                print(f"Error exporting Job \'{job.job_name}\': {e}")

        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON for line {line}: {e}")

print('-------------------------------------')

print('Done')
