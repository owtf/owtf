from __future__ import print_function
from sys import getsizeof, stderr
from itertools import chain
from collections import deque
import os
from datetime import datetime
import re

from ptp import PTP
from framework.dependency_management.dependency_resolver import ServiceLocator
from framework.db import models
from framework.db.target_manager import target_required

full_parse_tools = ['w3af', 'skipfish', 'arachni']

class PluginUploader():

	def __init__(self, tool_name):
		self.supported_tools = ['w3af', 'skipfish', 'arachni', 'hoppy', 'burpsuite']
		self.full_parse_tools = ['w3af', 'skipfish', 'arachni']
		self.db = ServiceLocator.get_component("db")
		self.transaction = ServiceLocator.get_component("transaction")
		self.re_extras = re.compile(r"^(\w+) (\/.*?) HT.*?")
		if tool_name in self.supported_tools:
			self.tool_name = tool_name
			self.ptp = PTP(tool_name)
		else:
			self.tool_name = None
			raise Exception("%s tool not supported by this plugin" % tool_name)

	def init_uploader(self, pathname):

		if self.tool_name in self.full_parse_tools:
			parsed_data = self.ptp.parse(pathname)
			self.parsed_data = parsed_data[1]
		else:
			self.parsed_data = self.ptp.parse(pathname)

	@target_required
	def OWTFDBUpload(self, target_id=None):
		if(target_id is None):
			print("Target id is None, aborting uploader!!")
			return;
		self.upload_checks()
		target_url = ServiceLocator.get_component("target").GetTargetURLForID(target_id)
		for data in self.parsed_data:
			extras = self.re_extras.findall(data['request'])[0]
			Method = extras[0]
			Url = target_url + extras[1]
			transaction_model = models.Transaction(
				url=Url,
				scope=None,
				method=Method,
				data=None,
				time=None,
				time_human="Uploaded by " + self.tool_name, # to distinguish uploader reports in transaction table
				local_timestamp=datetime.now(),
				raw_request=data['request'].decode('utf-8', 'ignore'),
				response_status=data['response_status_code'],
				response_headers=data['response_header'].decode('utf-8', 'ignore'),
				response_body=data['response_body'].decode('utf-8', 'ignore'),
				response_size=len(data['response_body']),
				binary_response=None,
				session_tokens=None,
				login=None,
				logout=None
				)
			transaction_model.target_id = target_id
			self.db.session.add(transaction_model)
		self.db.session.commit()
		print("Successfuly uploaded!!")

	def upload_checks(self):
		data_size = self.total_size(self.parsed_data)
		disk_status = self.disk_usage('/')
		percent_size = round((float(data_size)/disk_status['free'])*100, 1)
		if int(percent_size) <= 5:
			print("Uploading data size is less than 5%")
		elif int(percent_size) >= 99:
			raise Exception("Not enough space, aborting uploader")
		elif 90 < int(percent_size) < 99:
			print("WARNING!!! Uploading data is approx '%0.1f%%' size of free space available" % percent_size)
			cont = raw_input("Do you want to continue? y/n \n")
			if cont == 'n':
				raise Exception("Uploading aborted!")
			else:
				pass
		else:
			print("Uploading data is approx '%0.1f%%' size of free space available" % percent_size)
			cont = raw_input("Do you want to continue? y/n \n")
			if cont == 'n':
				raise Exception("Uploading aborted!")
			else:
				pass

	def total_size(self, o, handlers={}, verbose=False):
		""" Returns the approximate memory footprint an object and all of its contents.
		Automatically finds the contents of the following builtin containers and
		their subclasses:  tuple, list, deque, dict, set and frozenset.
		To search other containers, add handlers to iterate over their contents:
		handlers = {SomeContainerClass: iter,
		OtherContainerClass: OtherContainerClass.get_elements}
		"""
		dict_handler = lambda d: chain.from_iterable(d.items())
		all_handlers = {
			tuple: iter,
			list: iter,
			deque: iter,
			dict: dict_handler,
			set: iter,
			frozenset: iter,
		}
		all_handlers.update(handlers)     # user handlers take precedence
		seen = set()                      # track which object id's have already been seen
		default_size = getsizeof(0)       # estimate sizeof object without __sizeof__

		def sizeof(o):
			if id(o) in seen:       # do not double count the same object
				return 0
			seen.add(id(o))
			s = getsizeof(o, default_size)
			if verbose:
				print(s, type(o), repr(o), file=stderr)
			for typ, handler in all_handlers.items():
				if isinstance(o, typ):
					s += sum(map(sizeof, handler(o)))
					break
			return s

		return sizeof(o)

	def disk_usage(self, path):
		"""Return disk usage statistics about the given path.
		Returned valus is a named tuple with attributes 'total', 'used' and
		'free', which are the amount of total, used and free space, in bytes.
		"""
		st = os.statvfs(path)
		free = st.f_bavail * st.f_frsize
		total = st.f_blocks * st.f_frsize
		used = (st.f_blocks - st.f_bfree) * st.f_frsize
		disk_status = {'total': total, 'used': used, 'free': free}
		return disk_status


