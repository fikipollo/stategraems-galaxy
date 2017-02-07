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
		  4. dataset_id, the identifiers for the selected datasets
		  5. dataset_name, the names for the selected datasets
		  6. file_name, the file names for the selected datasets
		  7. upload_option, whether files should be uploaded or not to server
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
		"galaxy_username"  : params["user_name"],
		"origin"  : "galaxy",
		"apicode"  : params["emsuser"],
		"emsanalysisname"  : params["emsanalysisname"],
		"experiment_id"  : params["emsexperimentid"]
	}

	# 2.b. GENERATE THE PROVENANCE FOR THE FILE BASED ON THE HISTORY
	datasets_table = {}
	provenance_list = []
	already_added = {}
	selected_jobs = []
	#   2.b.i. Process the history data and generate the table output dataset -> job id
	#          and get the jobs that produces the selected datasets
	for job_id, job_instance in history_json.iteritems():
		for output_item in job_instance["outputs"]:
			datasets_table[output_item["id"]] = job_instance
			if output_item["id"] in metadata["dataset_id"]:
				selected_jobs.append(job_instance)

	#   2.b.ii. Get the provenance for each origin job
	for selected_job in selected_jobs:
		provenance_list = generateProvenance(selected_job, datasets_table, provenance_list, already_added)
	metadata["provenance"] = json.dumps(provenance_list);

	#STEP 3. UPLOAD THE PROVENANCE USING THE request lib
	if not(params["emshost"].startswith("http://") or params["emshost"].startswith("https://")):
		params["emshost"] = "http://" + params["emshost"]
	params["emshost"] = params["emshost"].rstrip("/")

	print "Sending provenance for datasets " + str(params["dataset_id"]) + " to EMS server " + params["emshost"] + " with user " + params["emsuser"]
	url = params["emshost"] + "/rest/analysis/import"
	headers = {'content-type': 'application/json'}
	response = requests.post(url, data=json.dumps(metadata), headers=headers)

	if(response.status_code != 200):
		print "Failed!"
		stop_err(response.status_code, response.text)

	response = response.json()
	analysis_id = response.get("newID")
	print "Success! New Analysis is " + analysis_id

	#STEP 4. UPLOAD THE FILES USING THE request lib
	if params["upload_option"] != "none":
		if params["upload_option"] == "all":
			jobs = already_added.values()
		else:
			jobs = selected_jobs

		for job in jobs:
			#FOR EACH OUTPUT external_filename -> TEST AND UPLOAD
			#AQUIIIIIII
			print "Sending file " + str(file) + " to EMS server " + params["emshost"] + " with user " + params["emsuser"]
			files = {'upload_file': open(str(file),'rb')}
			url = params["emshost"] + "/rest/files/"
			response = requests.post(url, files=files, params={'experiment_id' : params['emsexperimentid'], 'parent_dir': analysis_id, 'apicode' : params["emsuser"]})

			if(response.status_code != 200):
				#TODO: NOT FAIL OR THINK WHAT TO DO
				print "Failed!"
				stop_err(response.status_code, response.text)

	output=open(params["output_dir"], 'w+')
	output.write('<html><head></head><body>')
	output.write('<h1>This is a test</h1>')
	output.write('</body></html>')
	output.close()

	return True

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
		selected_job = datasets_table[input_item["id"]]
		generateProvenance(selected_job, datasets_table, provenance_list, already_added)

	return provenance_list

def stop_err( error_code, msg ):
    sys.stderr.write( "%s\n" % error_code )
    sys.stderr.write( "%s\n" % msg )
    sys.exit()

if __name__ == "__main__":
	main()
