"""
Refactoring utilitys
"""

import os
import jinja2
from jinja2 import Environment,PackageLoader
import dbapijinja


class ResponseObject:
	
	def __init__(self,status,body,headers=None,error=False):
		self.status = status
		self.body = body
		self.error = error
		if headers is None:
			self.headers = {}
		else:
			self.headers = headers
			
	def set_header(self,key,value):
		self.headers[key] = value
		
class RequestObject:
	
	def __init__(self):
		self.headers = {}
		self.query_string = None
		self.query_params = None
		
			
			
			
class DropacheException(Exception):
	
	def __init__(self,status,message=""):
		
		self.status = status
		self.message = message
		
		
		"""
		The index auto generator
		"""

		

def get_index_file(file_list,folder_path,client):

	
	jinja_env = Environment(loader=PackageLoader(__name__,'templates'))


	files = []
	for filemeta in file_list:
		file_name = os.path.basename(filemeta['path'])
		if filemeta['is_dir']:
			file_name = file_name + '/'
		files.append(file_name)

	dropbox_env = Environment(loader=dbapijinja.DropboxLoader(client,'/_templates'))

	try:
		custom_index_template = dropbox_env.get_template('index.html')
		return custom_index_template.render(files=files,path=folder_path)

	except jinja2.TemplateNotFound:
		index_template = jinja_env.get_template('index.html.tem')
		return index_template.render(files=files,path=folder_path)
		
