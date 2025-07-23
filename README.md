# streamsets-old-jobs-cleanup

This project provides three utility scripts that use the [IBM StreamSets SDK for Python](https://support-streamsets-com.s3.us-west-2.amazonaws.com/streamsets-docs/platform-sdk/latest/index.html) to clean up old Job instances from [IBM StreamSets](https://www.ibm.com/products/streamsets).  The scripts perform the following actions and are intended to be run in the following order to minimize risk when deleting Jobs:

- Script #1 [get-old-jobs.py](python/get-old-jobs.py): This script writes a list of Job instances whose last run was older than a user-defined look-back threshold, for example, a week or a month.

- Script #2 [export-old-jobs.py](python/export-old-jobs.py): This script exports old Job instances using the list created by script #1. The exports serve as backups in case any Job instances deleted by script #3 need to be restored.

- Script #3 [delete-old-jobs.py](python/delete-old-jobs.py): This script deletes old Job instances using the list created by script #1. The script will write a list of Job instances that were successfully deleted and those that were not. Note that Jobs that are referenced by [Sequences](https://www.ibm.com/docs/en/streamsets-controlhub?topic=run-sequences) or [Topologies](https://www.ibm.com/docs/en/streamsets-controlhub?topic=topologies-overview#concept_pvn_d1b_4w) can't be deleted, and will be captured in the list of unsuccessful deletion attempts.  The API credentials used to run this script must have at least read/write permissions on the Job instances being deleted. Job instances that were not deleted due to permission issues will also be listed.  

***
One could relatively easily club all three of those scripts together into a single script, and even add a "dry run" feature, but I chose to use three separate scripts so the critical "delete Job" logic can be easily inspected for correctness.  Additionally, this approach allows the user to edit the list of old Jobs created by the first script to control which Job instances will be deleted by the third script.
***


