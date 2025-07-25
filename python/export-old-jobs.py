#!/usr/bin/env python3
#################################################################
# FILE:  export-old-jobs.py
#
# DESCRIPTION:    This script exports the Jobs instances listed in the input file.
#
# ARGS:           - input_file - A JSON list of Job instances to export.  Note that Job Template
#                                Instances can't be exported, so they will be skipped.
#
#                 - export_dir - The directory to write the exported Jobs instances to.
#                                The directory will be created if it does not exist.
#                                If the directory does exist, it must be empty
#
# USAGE:          $ python3 export-old-jobs.py <input_file> <export_dir>
#
# USAGE EXAMPLE:  $ python3 export-old-jobs.py /Users/mark/old-jobs/old_jobs.json /Users/mark/jobs-export
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
def validate_input_file_parameter(the_input_file):
    file_path = Path(the_input_file)
    if file_path.is_file() and os.access(file_path, os.R_OK):
        return True
    else:
        print(f"Error: Input File \'{the_input_file}\' either does not exist or is not readable")
        return False

# Method that validates that the directory specified in the export_dir command line parameter either
# does not exist or exists but is an empty dir. If the directory does not exist it will be created.
# Returns True if the directory is OK or False if not.
def validate_export_dir_parameter(the_export_dir):

    # If export_dir already exists...
    if os.path.isdir(the_export_dir):
        # ... make sure it is empty
        if os.listdir(the_export_dir):
            print(f"Error: Export directory \'{the_export_dir}\' already exists but is not empty. ")
            print("Please specify a new or empty directory for Job export")
            return False

    # Create export dir if it does not yet exist
    else:
        try:
            os.makedirs(the_export_dir, exist_ok=True)
            if not os.path.isdir(the_export_dir):
                print("Error: directory creation failed.")
                return False
        except Exception as ex:
            print(f"Exception when trying to create directory \'{the_export_dir}\': {ex}")
            return False
    return True

#####################################
# Main Program
#####################################

# Get CRED_ID from the environment
CRED_ID = os.getenv('CRED_ID')

# Get CRED_TOKEN from the environment
CRED_TOKEN = os.getenv('CRED_TOKEN')

# Check the number of command line args
if len(sys.argv) != 3:
    print('Error: Wrong number of arguments')
    print('Usage: $ python3 export-old-jobs.py <input_file> <export_dir>')
    print('Usage Example: $ python3 export-old-jobs.py /Users/mark/old-jobs/old_jobs.json /Users/mark/jobs-export')
    sys.exit(1)

# Validate the input_file parameter
input_file = sys.argv[1]
print("---------------------------------")
print(f"input_file: '{input_file}'")
if not validate_input_file_parameter(input_file):
    sys.exit(1)

# Validate the export_dir parameter
export_dir = sys.argv[2]
print("---------------------------------")
print(f"export_dir: '{export_dir}'")
if not validate_export_dir_parameter(export_dir):
    sys.exit(1)

# Connect to Control Hub
print("---------------------------------")
print('Connecting to Control Hub')
sch = ControlHub(credential_id=CRED_ID, token=CRED_TOKEN)

print("---------------------------------")
print('Exporting Jobs...')
print("---------------------------------")

# Process each line of the input_file
with open(input_file, 'r') as f:
    for line in f:
        try:
            obj = json.loads(line)
            job_id = obj["job_id"]

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

                    # Skip this one if it is a Job Template Instance, wich can't be exported
                    if job.template_job_id is not None:
                        print(f"Skipping export for Job \'{job.job_name}\' because it is a Job Template Instance")
                        print(f"--> Job Template ID \'{job.template_job_id}\'")

                    # Not a Job Template Instance
                    else:

                        # replace '/' with '_' in Job name
                        job_name = job.job_name.replace("/", "_")
                        export_file_name = export_dir + '/' + job_name + '.zip'

                        print(f"Exporting Job \'{job.job_name}\' into the file \'{export_file_name}\'")

                        data = sch.export_jobs([job])

                        # Write a zip file for the Job
                        with open(export_file_name, 'wb') as file:
                            file.write(data)

            except Exception as e:
                print(f"Error exporting Job \'{job.job_name}\': {e}")

        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON for line {line}: {e}")

        print("---------------------------------")

print('Done')
