import os
import sys
import time
import json
from unittest import result
from unittest.signals import registerResult

from gradescope_utils.autograder_utils.json_test_runner import JSONTestResult

def load_meta_json(metadata_json = "/autograder/submission_metadata.json"):
	return json.load(open(metadata_json))

class NoStd():
    def __enter__(self):
        self._original_stdout = sys.stdout
        sys.stdout = open(os.devnull, 'w')

    def __exit__(self, exc_type, exc_val, exc_tb):
        sys.stdout.close()
        sys.stdout = self._original_stdout

class CustomJSONTestResult(JSONTestResult):
	def addError(self, test, err):
		super(JSONTestResult, self).addError(test, err)
		# Prevent output from being printed to stdout on failure
		self._mirrorOutput = False
		self.processResult(test, self.errors[-1]) # if err is used only a single, the last line is shown

class JSONTestRunner(object):
	"""A test runner class that displays results in JSON form.
	"""
	resultclass = CustomJSONTestResult

	def __init__(self, stream=sys.stdout, descriptions=True, verbosity=1,
				 failfast=False, buffer=True, visibility=None,
				 stdout_visibility=None, comment=""):
		"""
		Set buffer to True to include test output in JSON
		"""
		self.stream = stream
		self.descriptions = descriptions
		self.verbosity = verbosity
		self.failfast = failfast
		self.buffer = buffer
		self.json_data = {}
		self.json_data['output'] = comment
		self.json_data["tests"] = []
		self.json_data["leaderboard"] = []
		if visibility:
			self.json_data["visibility"] = visibility
		if stdout_visibility:
			self.json_data["stdout_visibility"] = stdout_visibility

	def _makeResult(self):
		return self.resultclass(self.stream, self.descriptions, self.verbosity,
								self.json_data["tests"], self.json_data["leaderboard"])

	def run(self, test):
		"Run the given test case or test suite."
		result = self._makeResult()
		registerResult(result)
		result.failfast = self.failfast
		result.buffer = self.buffer
		startTime = time.time()
		startTestRun = getattr(result, 'startTestRun', None)
		if startTestRun is not None:
			startTestRun()
		try:
			test(result)
		finally:
			stopTestRun = getattr(result, 'stopTestRun', None)
			if stopTestRun is not None:
				stopTestRun()
		stopTime = time.time()
		timeTaken = stopTime - startTime

		self.json_data["execution_time"] = format(timeTaken, "0.2f")

		total_score = 0
		for test in self.json_data["tests"]:
			total_score += test["score"]

		self.json_data["score"] = total_score

		json.dump(self.json_data, self.stream, indent=4)
		self.stream.write('\n')
		return result
