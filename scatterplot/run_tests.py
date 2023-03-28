import os
import sys
import json
import unittest
from datetime import datetime, timedelta
import yaml
from selenium import webdriver
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from skimage import data, transform, exposure, io
from skimage.util import compare_images
from utils.gs_helper import JSONTestRunner, load_meta_json
from utils.dropbox_helper import DropboxConnector

# To get an access token create a Dropbox App (https://dropbox.com/developers/apps)
ACCESS_TOKEN = ''

#db = DropboxConnector(ACCESS_TOKEN)

def get_assignment_config(config_filepath):
	with open(config_filepath, 'r') as stream:
		config = yaml.safe_load(stream)
	return config

def make_datetime(string):
	dt = datetime.strptime(string, "%Y-%m-%dT%H:%M:%S.%f%z")
	return offset_time(dt).replace(tzinfo=None)

def offset_time(sub_time):
	seconds_offset = -sub_time.utcoffset().seconds
	delta_hours = timedelta(hours=(24 + seconds_offset/3600))
	return sub_time + delta_hours

def check_interval(student_id, config, past_submissions):
	current_time = datetime.now()
	total_subs = config['total_submissions_limit']  	# 4
	sub_interval   = config['submissions_interval']		# 60 minutes
	if student_id in config['exceptions'].keys(): # overwrite if additional submission given
		total_subs = config['exceptions'][student_id]

	time_of_subs_within_limit = []
	for submission in past_submissions:
		sub_time = make_datetime(submission['submission_time'])
		# difference between past and current submission time
		delta_minutes = (current_time - sub_time).total_seconds() // 60
		
		try: # Check if it was graded (not a warning or info message)
			was_not_warning = submission["results"]["output"][:9] != "[WARNING]"
			was_not_info = submission["results"]["output"][:6] != "[INFO]"
			was_graded = was_not_warning and was_not_info
		except: # submission still running
			return True, 0, 0, 0

		is_timed_out = "Your submission timed out." in submission["results"]["output"]
		if is_timed_out: continue

		# Check if it was graded within last `sub_interval` minutes
		within_timelimit = delta_minutes < sub_interval

		if was_graded and within_timelimit:
			time_of_subs_within_limit.append(sub_time)

	submissions_made = len(time_of_subs_within_limit) + 1
	if submissions_made > total_subs:
		can_submit_again = False
		time_since_furthest_sub = (current_time - min(time_of_subs_within_limit)).seconds // 60
		till_next_sub = sub_interval - time_since_furthest_sub
	else:
		can_submit_again = True
		till_next_sub = 0

	return False, can_submit_again, till_next_sub, submissions_made


def upload_submission(submission_path, assignment_id, student_id, created_at):
	storage_full_path = '/submissions/'+assignment_id+'/'+student_id+'/'+created_at+'_'+"submission.html"
	db.upload_file(submission_path, storage_full_path)


def upload_submission_plot_render(submission_path, assignment_id, student_id, created_at):
	storage_full_path = '/submissions/'+assignment_id+'/'+student_id+'/'+created_at+'_'+"plot.png"
	db.upload_file(submission_path, storage_full_path)


def get_shared_render_link(submission_path, assignment_id, student_id, created_at):
	storage_full_path = '/submissions/' + assignment_id + '/' + student_id + '/' + created_at + '_' + "plot.png"
	return db.get_shared_link(storage_full_path)


def upload_metafile(metafile_path, assignment_id, student_id, created_at):
	storage_full_path = '/meta_files/'+assignment_id+'/'+student_id+'/'+created_at+'_'+"submission_metadata.json"
	db.upload_file(metafile_path, storage_full_path)


def get_shared_link(submission_path, assignment_id, student_id, created_at):
	storage_full_path = '/submissions/' + assignment_id + '/' + student_id + '/' + created_at + '_' + "submission.html"
	return db.get_shared_link(storage_full_path)


def compare_plots(plot_1_path:str, plot_2_path:str, save_path:str):
	"""adapted from:
	https://scikit-image.org/docs/dev/auto_examples/applications/plot_image_comparison.html#sphx-glr-auto-examples-applications-plot-image-comparison-py
	"""
	img1 = io.imread(plot_1_path)
	img1_equalized = exposure.equalize_hist(img1)
	img2 = io.imread(plot_2_path)

	blend_rotated = compare_images(img1, img2, method='blend')

	# blend compare
	fig = plt.figure(figsize=(8, 9))

	gs = GridSpec(3, 2)
	ax0 = fig.add_subplot(gs[0, 0])
	ax1 = fig.add_subplot(gs[0, 1])
	ax2 = fig.add_subplot(gs[1:, :])

	ax0.imshow(img1, cmap='gray')
	ax0.set_title('Solution')
	ax1.imshow(img2, cmap='gray')
	ax1.set_title('Submission')
	ax2.imshow(blend_rotated, cmap='gray')
	ax2.set_title('Blend comparison')
	for a in (ax0, ax1, ax2):
		a.axis('off')
	plt.tight_layout()
	plt.plot()
	plt.savefig(save_path)

if __name__ == '__main__':

	chrome_options = webdriver.ChromeOptions()
	chrome_options.add_argument('--no-sandbox')
	chrome_options.add_argument('--window-size=1000,550')
	chrome_options.add_argument('--headless')
	chrome_options.add_argument('--disable-gpu')

	if os.path.exists('/autograder'): # gradescope run
		local_run = False
		driver = webdriver.Chrome(options=chrome_options)
		metadata_json = "/autograder/submission_metadata.json"
		results_json = '/autograder/results/results.json'
	else:
		local_run = True
		driver = webdriver.Chrome(
			executable_path="utils/chromedriver",
			options=chrome_options)
		metadata_json = "sample/submission_metadata.json"
		results_json = 'sample/results.json'
	meta = load_meta_json(metadata_json)
	assignment_id = meta['assignment']['title'] 	# "scatterplot"
	created_at = meta['created_at'] 				 	# "2018-07-01T14:22:32.365935-07:00"
	student_email = meta['users'][0]['email'] 			# "studentname@gatech.edu"
	student_id = student_email.split('@')[0]			# "studentname"
	past_submissions = meta['previous_submissions']

	config = get_assignment_config('config/' + assignment_id + '/config.yaml')

	if local_run:
		still_running, can_submit_again, till_next_sub, submissions_made = False, True, 1, 1
	else:
		still_running, can_submit_again, till_next_sub, submissions_made = check_interval(student_id, config, past_submissions)
	total_subs = config['total_submissions_limit']
	if still_running:
		comment = f"""
[INFO] One of your previous submissions is still running. Please wait until it terminates and try again.
"""
		json_data = {}
		json_data["output"] = comment
		json_data["score"] = 0.0
		json.dump(json_data, open(results_json, 'w'), indent=4)
	elif can_submit_again:
		comment = f"Submission {submissions_made} out of {total_subs} during {config['submissions_interval']} minute interval"
		# Grade submission
		sys.path.append(assignment_id) # Make the subfolder .py files importable (e.g. isolation.py)
		sys.path.append('submission/') # Make the subfolder with submission file importable

		# take screenshot of submission
		url = 'http://localhost:8080/submission.html'
		driver.get(url)
		driver.save_screenshot('submission/plot.png')
		driver.quit()

		if not local_run:
			compare_plots("solution/solution_plot.png", "submission/plot.png", "submission/comparison.png")
			upload_submission("submission/submission.html", assignment_id, student_id, created_at)
			upload_submission_plot_render("submission/comparison.png", assignment_id, student_id, created_at)
			upload_metafile(metadata_json, assignment_id, student_id, created_at)
		try:
			shared_plot_link = get_shared_render_link("submission/comparison.png", assignment_id, student_id, created_at)
			print('shared plot link: ', shared_plot_link.url)
			comment = comment + f"""\n Use this link to view a screenshot of your visualization	: <a href='{shared_plot_link.url}'>Dropbox</a> <br />This link will only be displayed once."""
		except:
			comment = comment + "\n Could not get shared link for plot screenshot. This submission already has a screenshot shared from a previous gradescope run."

		suite = unittest.defaultTestLoader.discover('scatterplot/tests')  # just using 'tests' could include unwanted tests
		with open(results_json, 'w') as f:
			tests = JSONTestRunner(
				stream=f,
				stdout_visibility='hidden',
				visibility='visible',
				comment=comment,
				).run(suite)
	else:
		comment = f"""
		[WARNING] You have reached the submission limit ({total_subs}/{total_subs}). 
		Please wait for {till_next_sub} minutes and then resubmit.
		"""
		json_data = {}
		json_data["output"] = comment
		json_data["score"] = 0.0
		json.dump(json_data, open(results_json, 'w'), indent=4)
