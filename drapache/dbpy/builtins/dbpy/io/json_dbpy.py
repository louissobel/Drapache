
import json
import sys

name = 'json'


__doc__ = "Functions for working with json files that live on dropbox"

def build(env,path):
	
	
	self = env.get_new_module(path+'.'+name)
	
	file = env.get_module('dbpy.io.file')
	http = env.get_module('dbpy.http')
	
	@env.register(self)
	def open(path,from_data=None,timeout=None,default=dict):
		"""
		opens a json dictionary or list, returning a data-handle. Any changes to that
		dictionary or list will be updated back to dropbox once the file handle is closed.
		It can only be a dictionary or list because primitives are hard to keep a reference to in python,
		a work-around for this would be nice.
		Raises an `IOError` if something goes wrong, or a `ValueError` if the json is bad
		
		Use `from_data` to open up a json file from an existing dictionary or list.
		
		If `path` does not exist, it will be created
		"""
		
		out_json = None	
		try:
			if from_data is None:
				json_file = file.open(path,to='json',timeout=timeout) 
				out_json = json_file.json_object
			else:
				json_file = file.open(path,to='json',timeout=Timeout,allow_download=False)
				json_file.json_object = from_data
				out_json = from_data
			
		except IOError as e:
			raise IOError("Unable to open JSON object backed by writable file:\n%s"%e.message)
		except ValueError as e:
			raise ValueError("Error parsing json file")
			
		if out_json is None:
			out_json = default()
			json_file.json_object = out_json
		
		if not (isinstance(out_json,dict) or isinstance(out_json,list)):
			raise ValueError("You can only open a json that is a dictionary or a list")
			
		return out_json
		
	@env.register(self)
	def open_list(path,from_data=None,timeout=None):
		"""
		Opens a json list. A strange, slightly redundant function. I've disliked it ever since I wrote it,
		but I can't bring myself to delete it for some reason."""
		out =  self.open(path,from_data=from_data,timeout=timeout,default=list)
		if not isinstance(out,list):
			raise ValueError("Object opened by open_list is not a list!")
		return out
	

		
	@env.register(self)
	@env.privileged
	def close(inner_dict):
		"""
		Closes the json file handle. This will happen automatically, but this releases locks and resources
		"""
		#look through all the registered open files (file.open adds to this list)
		#and see if the json dictionary we are dealing  with this matches, (then close it if so)
		for open_file_h in env.locker.open_files:
			if hasattr(open_file_h,'json_object'):
				if open_file_h.json_object is inner_dict:
					open_file_h._close(env.locker)
		
	@env.register(self)
	@env.privileged
	def save(path,json_object,timeout=None):
		"""
		Takes any json object and writes it to the given path
		"""
		json_file = file.open(path,to='json',timeout=timeout,allow_download=False)
		json_file.json_object = json_object
		close(json_object) #because of the way that close ^^ works, we pass the dictionary, not the file handle itself
	
	@env.register(self)
	@env.privileged
	def load(path):
		"""
		loads a json file and returns it
		throws a ValueError if the json file is not valid
		"""
		try:
			return json.load(file.open(path))
		except ValueError:
			raise ValueError('Unable to parse json file')
			
	@env.register(self)
	def render(path):
		"""
		Renders the given json path to stdout
		With the proper Content-Type
		"""
		http.set_response_header('Content-Type','application/json')
		sys.stdout.write(file.read(path))
			
	return self