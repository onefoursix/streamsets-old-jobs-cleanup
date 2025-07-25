# streamsets-old-jobs-cleanup

This project provides three utility scripts that use the [IBM StreamSets SDK for Python](https://support-streamsets-com.s3.us-west-2.amazonaws.com/streamsets-docs/platform-sdk/latest/index.html) to clean up old Job Instances and Job Template Instances from [IBM StreamSets](https://www.ibm.com/products/streamsets).  This clean up is often needed, particularly if one has large numbers of Job Template Instances created with the setting <code>Delete from Job Instances List when Completed</code> disabled.

The scripts perform the following actions and are intended to be run in the following order to minimize risk when deleting Jobs:

- Script #1 [get-old-jobs.py](python/get-old-jobs.py): This script writes a list of Job instances whose last run was older than a user-defined look-back threshold, for example, a week or a month.

- Script #2 [export-old-jobs.py](python/export-old-jobs.py): This script exports the Job instances in the list created by script #1. The exports serve as backups in case any Job instances deleted by script #3 need to be restored. Note that Job Template Instances can't be exported, but deleting Job Template Instances (as performed by script #3) does not delete the associated Job Templates.

- Script #3 [delete-old-jobs.py](python/delete-old-jobs.py): This script deletes the Job instances in the list created by script #1. The script will write a list of Job instances that were successfully deleted and those that were not. Note that Jobs that are referenced by [Sequences](https://www.ibm.com/docs/en/streamsets-controlhub?topic=run-sequences) or [Topologies](https://www.ibm.com/docs/en/streamsets-controlhub?topic=topologies-overview#concept_pvn_d1b_4w) can't be deleted.  The API credentials used to run this script must have at least read/write permissions on the Job instances in order to delete them. Job instances that were not deleted due to permission issues will also be listed.  

***
Note that all three of these scripts could relatively easily be clubbed together into a single script, and one could add a "dry run" feature, but I chose to use three separate scripts so the critical "delete Job" logic (in script #3) could more easily be inspected for correctness.  Additionally, this approach allows the user to edit the list of old Jobs created by the first script to control which Job instances will be deleted by the third script.

Note also that the scripts rely on an external file to pass around the list of Jobs, rather than using Jog tags to flag Job instances for deletion.  This approach is needed because one can't currently add tags to Job Template Instances.
***

See the details for running each script below.

## PREREQUISITES

- Python 3.9+

- StreamSets Platform SDK for Python v6.6+. Docs are [here](https://docs.streamsets.com/platform-sdk/latest/welcome/installation.html)

 - StreamSets Platform API Credentials for a user with at least read/write permissions for the Jobs to be deleted.

 - Before running any of the scripts, export the environment variables <code>CRED_ID</code> and <code>CRED_TOKEN</code>
  with StreamSets Platform API Credentials, like this:
```
    	$ export CRED_ID="40af8..."
    	$ export CRED_TOKEN="eyJ0..."
```

## Script #1 - get-old-jobs.py

Description:   This script writes a list of INACTIVE Job instances that have not been run within a user-defined lookback period, for example, a week or a month. The list of old Job instances is written in to a JSON file on the local file system. Job instances that have not yet been run are ignored as they may have just been created.

Args:

- <code>last_run_threshold</code> - The threshold date to mark Jobs as needing to be cleaned up if the Job's last run was before that date.

- <code>output_file</code> - The full path to a file where the list of old jobs will be written. Directories in the path will be created as needed, and if an existing file of the same name exists, it will be overwritten.

Usage:          <code>$ python3 get-old-jobs.py <last_run_threshold> <output_file></code> 

Usage Example:  <code>$ python3 get-old-jobs.py 2024-06-30 /Users/mark/old-jobs/old_jobs.json</code> 

Example Run:
```
	$ python3 get-old-jobs.py 2025-07-22 /Users/mark/old-jobs/old_jobs.json 
	---------------------------------
	last_run_threshold: '2025-07-22'
	---------------------------------
	Output file: '/Users/mark/old-jobs/old_jobs.json'
	---------------------------------
	Connecting to Control Hub
	---------------------------------
	Searching for old Jobs (this may take a while)...
	---------------------------------
	Job: 'Check API Schema - http://localhost:9001/get/employee' Last Run Date: 2025-07-10 16:07:26
	Job: 'Check API Schema - http://localhost:9001/get/employee' Last Run Date: 2025-07-10 16:09:21
	Job: 'Check API Schema - http://localhost:9002/movies' Last Run Date: 2025-07-10 16:08:14
	Job: 'Check Database Table Schema - employee' Last Run Date: 2025-07-16 10:07:35
	Job: 'Check Database Table Schema - employee' Last Run Date: 2025-07-14 08:43:18
	Job: 'Oracle CDC to Snowflake' Last Run Date: 2024-05-29 10:08:11
	Job: 'Oracle to Snowflake Bulk Load' Last Run Date: 2024-05-26 10:42:05
	Job: 'Weather to MongoDB' Last Run Date: 2023-01-12 19:07:00
	---------------------------------
	Writing the list of old Job Instances to the output file in sorted date order (oldest first)
	---------------------------------
	Done

```
Here is an example of the data written to the output file <code>old_jobs.json</code>. Note that the Jobs are sorted with the oldest last run time first:

```
	{"last_run": "2023-01-12 19:07:00", "job_name": "Weather to MongoDB", "job_id": "338b33a1-1ad6-47a0-9b66-6b685921d3fc:8030c2e9-1a39-11ec-a5fe-97c8d4369386", "last_run_threshold": "2025-07-22"}
	{"last_run": "2024-05-26 10:42:05", "job_name": "Oracle to Snowflake Bulk Load", "job_id": "fe9605ab-4912-4181-a315-e49d031a0d50:8030c2e9-1a39-11ec-a5fe-97c8d4369386", "last_run_threshold": "2025-07-22"}
	{"last_run": "2024-05-29 10:08:11", "job_name": "Oracle CDC to Snowflake", "job_id": "00d5d750-527e-4ac3-9417-4b0dcbfcab35:8030c2e9-1a39-11ec-a5fe-97c8d4369386", "last_run_threshold": "2025-07-22"}
	{"last_run": "2025-07-10 16:07:26", "job_name": "Check API Schema - http://localhost:9001/get/employee", "job_id": "6641429e-dea4-416e-a93a-d4bdc5f98eaf:8030c2e9-1a39-11ec-a5fe-97c8d4369386", "last_run_threshold": "2025-07-22"}
	{"last_run": "2025-07-10 16:08:14", "job_name": "Check API Schema - http://localhost:9002/movies", "job_id": "3687eba0-9a76-457c-ad5a-56424cac8181:8030c2e9-1a39-11ec-a5fe-97c8d4369386", "last_run_threshold": "2025-07-22"}
	{"last_run": "2025-07-10 16:09:21", "job_name": "Check API Schema - http://localhost:9001/get/employee", "job_id": "4082cfa9-f622-4f83-a1a1-9bacfe10a2a6:8030c2e9-1a39-11ec-a5fe-97c8d4369386", "last_run_threshold": "2025-07-22"}
	{"last_run": "2025-07-14 08:43:18", "job_name": "Check Database Table Schema - employee", "job_id": "6b3a84fd-b72f-4ab4-a2a3-10850dd3f88e:8030c2e9-1a39-11ec-a5fe-97c8d4369386", "last_run_threshold": "2025-07-22"}
	{"last_run": "2025-07-16 10:07:35", "job_name": "Check Database Table Schema - employee", "job_id": "bf8aa913-eca9-45f6-8cea-9ce7bff82326:8030c2e9-1a39-11ec-a5fe-97c8d4369386", "last_run_threshold": "2025-07-22"}

```

## Script #2 - export-old-jobs.py

Description:   This script exports the Jobs instances listed in the input file. Note that Job Template Instances can't be exported, so they will be skipped.
Args:

- <code>input_file</code> - A JSON list of Job instances to export (i.e. the output file written by script #1)

- <code>export_dir</code> - The directory to write the exported Jobs instances to. The directory will be created if it does not exist. If the directory does exist, it must be empty

Usage:          <code>$ python3 export-old-jobs.py <input_file> <export_dir></code> 

Usage Example:  <code>$ python3 export-old-jobs.py /Users/mark/old-jobs/old_jobs.json /Users/mark/jobs-export</code>

This script does not write a log, so if you want to capture the results of this script in a file, redirect its output like this:

<code>$ python3 export-old-jobs.py /Users/mark/old-jobs/old_jobs.json /Users/mark/jobs-export > /Users/mark/job-exports.log</code> 

Example Run:
```
	$ python3 export-old-jobs.py /Users/mark/old-jobs/old_jobs.json /Users/mark/job-exports 
	---------------------------------
	input_file: '/Users/mark/old-jobs/old_jobs.json'
	---------------------------------
	export_dir: '/Users/mark/job-exports'
	---------------------------------
	Connecting to Control Hub
	---------------------------------
	Exporting Jobs:
	---------------------------------
	Exporting Job 'Weather to MongoDB' into the file '/Users/mark/job-exports/Weather to MongoDB.zip'
	Exporting Job 'Weather Raw to Refined (1)' into the file '/Users/mark/job-exports/Weather Raw to Refined (1).zip'
	Exporting Job 'Weather Aggregation' into the file '/Users/mark/job-exports/Weather Aggregation.zip'
	Exporting Job 'Oracle to Snowflake Bulk Load' into the file '/Users/mark/job-exports/Oracle to Snowflake Bulk Load.zip'
	Exporting Job 'Oracle CDC to Snowflake' into the file '/Users/mark/job-exports/Oracle CDC to Snowflake.zip'
	-------------------------------------
	Done

```

If you have Job Template Instances in the list of old Jobs, you will see messages like this when you run the script:

```
	---------------------------------
	Skipping export for Job 'Check Database Table Schema - employee' because it is a Job Template Instance
	--> Job Template ID '97ec0a88-4e19-4855-aece-3a9b13f390d7:8030c2e9-1a39-11ec-a5fe-97c8d4369386'
	---------------------------------
```

Here is a directory listing of the exported Jobs:

```
	$ ls -l ~/job-exports
	total 888
	-rw-r--r--@ 1 mark  staff   90414 Jul 23 14:43 Oracle CDC to Snowflake.zip
	-rw-r--r--@ 1 mark  staff  135891 Jul 23 14:43 Oracle to Snowflake Bulk Load.zip
	-rw-r--r--@ 1 mark  staff   52758 Jul 23 14:43 Weather Aggregation.zip
	-rw-r--r--@ 1 mark  staff  105615 Jul 23 14:43 Weather Raw to Refined (1).zip
	-rw-r--r--@ 1 mark  staff   59928 Jul 23 14:43 Weather to MongoDB.zip
```

A good test to perform at this point is to manually delete one of those Job instances from Control Hub and to import the corresponding exported file using the Control Hub UI to confirm the exported Job archives are valid, like this:

<img src="images/import1.png" alt="import1.png" width="700"/>
<img src="images/import2.png" alt="import2.png" width="700"/>


## Script #3 - delete-old-jobs.py

Description:   This script attempts to delete Jobs instances listed in the input file.  Job Instances and Job Template Instances will be deleted, unless there are permission issues, or in cases where Job instances are referenced by Sequences or Topologies. 

Args:
- <code>input_file</code> - A JSON list of Job instances to delete.

Usage:          <code>$ python3 delete-old-jobs.py <input_file></code>

Usage Example:  <code>$ python3 delete-old-jobs.py /Users/mark/old-jobs/old_jobs.json</code>

This script does not write a log, so if you want to capture the results of this script in a file, redirect its output like this:

$ python3 delete-old-jobs.py /Users/mark/old-jobs/old_jobs.json > /Users/mark/deleted-jobs.log

A good test to perform at this point is to manually edit an old_jobs.json input file so there are only a couple of Jobs listed, and to run the script and confirm that those Jobs were correctly deleted.


Example Run:
```
	$ python3 python/delete-old-jobs.py /Users/mark/old-jobs/old_jobs.json 
	---------------------------------
	input_file: '/Users/mark/old-jobs/old_jobs.json'
	---------------------------------
	Connecting to Control Hub
	Preparing to delete Job 'Weather to MongoDB' with Job ID '338b33a1-1ad6-47a0-9b66-6b685921d3fc:8030c2e9-1a39-11ec-a5fe-97c8d4369386'
	- Found Job
	- Job has status 'INACTIVE'
	Error: Attempt to delete Job failed; JOBRUNNER_251: Cannot delete job 'Weather to MongoDB' as it is part of sequences: '1'
	---------------------------------
	Preparing to delete Job 'Check API Schema - http://localhost:9001/get/employee' with Job ID '6641429e-dea4-416e-a93a-d4bdc5f98eaf:8030c2e9-1a39-11ec-a5fe-97c8d4369386'
	- Found Job
	- Job has status 'INACTIVE'
	- Job was deleted.
	---------------------------------
	Preparing to delete Job 'Check API Schema - http://localhost:9002/movies' with Job ID '3687eba0-9a76-457c-ad5a-56424cac8181:8030c2e9-1a39-11ec-a5fe-97c8d4369386'
	- Found Job
	- Job has status 'INACTIVE'
	- Job was deleted.
	---------------------------------
	Preparing to delete Job 'Check API Schema - http://localhost:9001/get/employee' with Job ID '4082cfa9-f622-4f83-a1a1-9bacfe10a2a6:8030c2e9-1a39-11ec-a5fe-97c8d4369386'
	- Found Job
	- Job has status 'INACTIVE'
	- Job was deleted.
	---------------------------------
	Preparing to delete Job 'Check Database Table Schema - employee' with Job ID '6b3a84fd-b72f-4ab4-a2a3-10850dd3f88e:8030c2e9-1a39-11ec-a5fe-97c8d4369386'
	- Found Job
	- Job has status 'INACTIVE'
	- Job was deleted.
	---------------------------------
	Preparing to delete Job 'Check Database Table Schema - employee' with Job ID 'bf8aa913-eca9-45f6-8cea-9ce7bff82326:8030c2e9-1a39-11ec-a5fe-97c8d4369386'
	- Found Job
	- Job has status 'INACTIVE'
	- Job was deleted.
	---------------------------------
	Done
```


