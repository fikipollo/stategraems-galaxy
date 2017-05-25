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
		  1. ems_host, the STATegra EMS host
		  2. ems_api_code, the STATegra EMS user API code
		  3. ems_analysis_name, the name for the new analysis
		  4. ems_experiment_id, the ID for the experiment
		  5. selected_dataset_id, the identifiers for the selected datasets
		  6. upload_option, whether files should be uploaded or not to server
		  7. user_name, current Galaxy username
		  8. history_id, the current history identifier
		  9. job_working_dir, the working dir for the current job
		 10. output_file, the output file for the job
	 -- sys.argv[2] is the current Galaxy history in JSON-like format
	"""

	#STEP 1. Read the params
	params = json.loads(sys.argv[1])
	with open(params["job_working_dir"] + '.tmp') as data_file:
	    history_json = json.load(data_file)

	#PREPARE THE PARAMS FOR THE OUTPUT FILE
	output_params = {
		'analysis_registration_status_title' : "",
		'analysis_registration_status_message' : "",
		'analysis_registration_name' : params['ems_analysis_name'],
		'analysis_registration_id' : "",
		'analysis_registration_link' : "",
		'submission_status_title' : "<h3>No files were submitted</h3>",
		'submission_status_message' : "",
		'submission_files_list' : ""
	}

	try:

		#STEP 2. COMPLETE THE METADATA FOR THE FILE USING THE GALAXY API
		# 2.a. FROM INPUT PARAMS
		metadata = {
			"history_id" : params["history_id"],
			"selected_dataset_id" : params["selected_dataset_id"],
			"galaxy_username"  : params["user_name"],
			"origin"  : "galaxy",
			"apicode"  : params["ems_api_code"],
			"ems_analysis_name"  : params["ems_analysis_name"],
			"experiment_id"  : params["ems_experiment_id"]
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
				if output_item["id"] in metadata["selected_dataset_id"]:
					selected_jobs.append(job_instance)

		#   2.b.ii. Get the provenance for each origin job
		for selected_job in selected_jobs:
			provenance_list = generateProvenance(selected_job, datasets_table, provenance_list, already_added)
		metadata["provenance"] = json.dumps(provenance_list);

		#STEP 3. UPLOAD THE PROVENANCE USING THE request lib
		if not(params["ems_host"].startswith("http://") or params["ems_host"].startswith("https://")):
			params["ems_host"] = "http://" + params["ems_host"]
		params["ems_host"] = params["ems_host"].rstrip("/")

		print "Registering a new analysis..."
		url = params["ems_host"] + "/rest/analysis/import"
		headers = {'content-type': 'application/json'}
		response = requests.post(url, data=json.dumps(metadata), headers=headers)

		if(response.status_code != 200):
			print "Failed!"
			raise Exception(response.text)
		else:
			response = response.json()
			analysis_id = response.get("newID")
			print "Success!"
			print "The ID for the new Analysis is " + analysis_id
			output_params["analysis_registration_status_title"] = '<h3 class="text-success"><span class="glyphicon glyphicon-ok-sign"></span> Success</h3>'
			output_params["analysis_registration_status_message"] = 'A new analysis has been successfully created in the selected STATegra EMS instance.'
			output_params["analysis_registration_id"] = analysis_id
			output_params["analysis_registration_link"] = '<a href="' + params["ems_host"] + "/#/analysis" + '" target="_blank"> Show in STATegra EMS</a>'

		#STEP 4. UPLOAD THE FILES USING THE request lib
		errors = []
		print "Uploading files..."
		if params["upload_option"] == "none":
			print "No files were uploaded"
		else:
			if params["upload_option"] == "all":
				jobs = already_added.values()
			else:
				jobs = selected_jobs

			for job in jobs:
				#FOR EACH OUTPUT external_filename -> TEST AND UPLOAD
				for file in job["outputs"]:
					file_name = file["file"].replace(" ", "_") + "." + file["extension"]
					print " - " + str(file_name)
					files = {'upload_file': open(str(file["file_name"]),'rb')}
					url = params["ems_host"] + "/rest/files/"
					response = requests.post(url, files=files, params={'file_name' : file_name, 'experiment_id' : params['ems_experiment_id'], 'parent_dir': analysis_id, 'apicode' : params["ems_api_code"]})

					if(response.status_code != 200):
						print "   FAILED"
						errors.append('<li>Failed while uploading the file "' + file_name + '", the file was not uploaded.</li>')
					else:
						print "   OK"
						output_params["submission_files_list"] += '<tr><td>' + file_name + '</tr></td>'

			if len(errors) > 0:
				print "Errors detected, please check output for details."
				output_params["submission_status_title"] = '<h3 class="text-warning"><span class="glyphicon glyphicon-info-sign"></span> Errors detected</h3>'
				output_params["submission_status_message"] = '<p>Some errors were detected while uploading files</p><ul>' + "\n".join(errors) + '</ul>'
			else:
				output_params["submission_status_title"] = '<h3 class="text-success"><span class="glyphicon glyphicon-ok-sign"></span> Success</h3>'
				output_params["submission_status_message"] = '<p>All files were uploaded successfully.</p>'

		generateOutputFile(params["output_file"], output_params)

	except Exception as e:
		output_params["analysis_registration_status_title"] = '<h3 class="text-danger"><span class="glyphicon glyphicon-remove-sign"></span> Failed</h3>'
		output_params["analysis_registration_status_message"] = 'Error message: ' + str(e)
		generateOutputFile(params["output_file"], output_params)
		stop_err(str(e))

	return True

def generateProvenance(job_instance, datasets_table, provenance_list, already_added):
	"""
	This function generates the provenance for a given dataset from a the Galaxy history.
	Starting from the job that results in the dataset, the script goes back in the history
	selecting all the jobs whose results were used to produce the final dataset.
	"""
	#if not in provenance_list --> push
	if not job_instance["id"] in already_added:
		already_added[job_instance["id"]] = job_instance
		provenance_list.append(job_instance)

	#Get the input files
	#For each input file, get the origin job
	for input_item in job_instance["inputs"]:
		selected_job = datasets_table[input_item["id"]]
		if "file" in input_item:
			selected_job["step_name"] =  input_item["file"]
		generateProvenance(selected_job, datasets_table, provenance_list, already_added)

	return provenance_list

def generateOutputFile(output_file, output_params):
	import os
	path = os.path.realpath(__file__)
	path = os.path.dirname(path)

	from string import Template
	#open the file
	template = open(path + '/result.tmp.html')
	#read it
	src = Template( template.read() )
	#do the substitution
	result = src.substitute(output_params)
	#Save the content to the output file
	output=open(output_file, 'w+')
	output.write(result)
	output.close()

def stop_err(msg):
    sys.stderr.write( "%s\n" % msg )
    sys.exit()

if __name__ == "__main__":
	main()
