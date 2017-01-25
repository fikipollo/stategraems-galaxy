#!/usr/bin/python
'''
   The MIT License (MIT)

   Copyright (c) 2016 SLU Global Bioinformatics Centre, SLU

   Permission is hereby granted, free of charge, to any person obtaining a copy
   of this software and associated documentation files (the "Software"), to deal
   in the Software without restriction, including without limitation the rights
   to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
   copies of the Software, and to permit persons to whom the Software is
   furnished to do so, subject to the following conditions:

   The above copyright notice and this permission notice shall be included in all
   copies or substantial portions of the Software.

   THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
   IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
   FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
   AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
   LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
   OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
   SOFTWARE.

   Contributors:
      Rafa Hernandez de Diego <https://github.com/fikipollo>
      Tomas Klingstrom
      Erik Bongcam-Rudloff
	  Ana Conesa Cegarra
      and others.

	  A Galaxy tool to store files in an external STATegra EMS server.
'''

import sys
import json
import requests

def main():
	"""
	This function reads the params and sends a file from the Galaxy history to an
	STATegra EMS server
	Note: this tool requires the python-request package installed in the Galaxy instance.
	The accepted params are:
	 -- sys.argv[0] is the python script
	 -- sys.argv[1] is a JSON-like string containing the params for the script
		  1. emshost, the STATegra EMS host
		  2. emsuser, the STATegra EMS user
		  3. history_id, the current history identifier
		  4. dataset_id, the identifier for the selected dataset
		  5. dataset_name, the name for the selected dataset
		  6. file_name, the file name for the selected dataset
		  7. file_format, the file format for the selected dataset
		  8. output_dir, the dir for the output files for current job
		  9. user_name, current Galaxy username
		 10. emsanalysisname, the name for the new analysis
		 11. emsexperimentid, the ID for the experiment
	 -- sys.argv[2] is the current Galaxy history in JSON-like format
	"""
	#STEP 1. Read the params
	params = json.loads(sys.argv[1])
	with open(params["output_dir"] + '.tmp') as data_file:
	    history_json = json.load(data_file)

	#STEP 2. COMPLETE THE METADATA FOR THE FILE USING THE GALAXY API
	# 2.a. FROM INPUT PARAMS
	metadata = {
		"history_id" : params["history_id"],
		"dataset_id" : params["dataset_id"],
		"format"     : params["file_format"],
		"galaxy_username"  : params["user_name"],
		"origin"  : "galaxy",
		"username"  : params["emsuser"],
		"emsanalysisname"  : params["emsanalysisname"],
		"experiment_id"  : params["emsexperimentid"]
	}

	# 2.b. GENERATE THE PROVENANCE FOR THE FILE BASED ON THE HISTORY
	datasets_table = {}
	provenance_list = []
	already_added = {}
	origin_job = None
	#   2.b.i. Process the history data and generate the table dataset -> job id
	for job_id, job_instance in history_json.iteritems():
		for output_item in job_instance["outputs"]:
			datasets_table[output_item["id"]] = job_instance
			if output_item["id"] == metadata["dataset_id"]:
				origin_job=job_instance

	#   2.b.ii. Get the origin job
	provenance_list = generateProvenance(origin_job, datasets_table, provenance_list, already_added)
	metadata["provenance"] = json.dumps(provenance_list);

	#STEP 3. UPLOAD THE FILE USING THE request lib
	if not(params["emshost"].startswith("http://") or params["emshost"].startswith("https://")):
		params["emshost"] = "http://" + params["emshost"]
	params["emshost"] = params["emshost"].rstrip("/")

	print "Sending file " + params["file_name"] + " to EMS server " + params["emshost"] + " with user " + params["emsuser"]
	url = params["emshost"] + "/rest/analysis/import"
	headers = {'content-type': 'application/json'}

	r = requests.post(url, data=json.dumps(metadata), headers=headers)

	if(r.status_code != 200):
		stop_err(r.status_code, r.text)

	return (r.status_code == 200)

def generateProvenance(job_instance, datasets_table, provenance_list, already_added):
	"""
	This function generates the provenance for a given dataset from a the Galaxy history.
	Starting from the job that results in the dataset, the script goes back in the history
	selecting all the jobs whose results were used to produce the final dataset.
	"""
	#if not in provenance_list --> push
	if not job_instance["id"] in already_added:
		already_added[job_instance["id"]] = 1
		provenance_list.append(job_instance)

	#Get the input files
	#For each input file, get the origin job
	for input_item in job_instance["inputs"]:
		origin_job = datasets_table[input_item["id"]]
		generateProvenance(origin_job, datasets_table, provenance_list, already_added)

	return provenance_list

def stop_err( error_code, msg ):
    sys.stderr.write( "%s\n" % error_code )
    sys.stderr.write( "%s\n" % msg )
    sys.exit()

if __name__ == "__main__":
	main()
