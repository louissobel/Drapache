"""
The index auto generator
"""
import os
import jinja2
from jinja2 import Environment,PackageLoader
import dbapijinja

jinja_env = Environment(loader=PackageLoader(__name__,'templates'))

def get_index_file(file_list,folder_path,client):
	
	
	
	
	files = []
	for filemeta in file_list:
		file_name = os.path.basename(filemeta['path'])
		if filemeta['is_dir']:
			file_name = file_name + '/'
		files.append(file_name)
		
	dropbox_env = jinja2.Environment(loader=dbapijinja.DropboxLoader(client,'/_templates/'))
	
	try:
		custom_index_template = dropbox_env.get_template('index.html')
		return custom_index_template.render(files=files,path=folder_path)
	
	except jinja2.TemplateNotFound:
		index_template = jinja_env.get_template('index.html.tem')
		return index_template.render(files=files,path=folder_path)