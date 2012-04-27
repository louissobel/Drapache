
import json

name = 'json'


def build(env,path):
	
	
	self = env.get_new_module(path+'.'+name)
	
	file = env.get_module('dbpy.io.file')
	
	@env.register(self)
	def open(path,from_data=None,timeout=None,default=dict):
		#opens up a json file handle of sorts
		#it will be backed by a WritableDropboxFile
		
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
	def new_list(path,from_data=None,timeout=None):
		out =  file.open(path,from_data=from_data,timeout=timeout,default=list)
		if not isinstance(out,list):
			raise ValueError("Object opened by open_json_list is not a list!")
	

		
	@env.register(self)
	@env.privileged
	def close(inner_dict):
		for open_file_h in env.locker.open_files:
			if hasattr(open_file_h,'json_object'):
				if open_file_h.json_object is inner_dict:
					open_file_h._close(env.locker)
		
	@env.register(self)
	@env.privileged
	def save(path,json_object,timeout=None):
		json_file = file.open(path,to='json',timeout=timeout,allow_download=False)
		json_file.json_object = json_object
		close(json_file)
	
	@env.register(self)
	@env.privileged
	def load(path):
		"""
		loads a json file and returns it
		throws a ValueError if the json file fucks up
		"""
		try:
			return json.load(file.open(path))
		except ValueError:
			raise ValueError('Unable to parse json file')
			
			
	return self