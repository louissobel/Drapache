"""
The class that allows templateing from dropbox
"""
import jinja2
import os
import dropbox

class TemplateNotFound(Exception):
	pass

class DropboxLoader(jinja2.BaseLoader):
	
	
	def __init__(self,client,search_root):
		self.client = client
		self.search_root = search_root		
		
	def get_source(self,environment,path):
			
			
		template_path = self.search_root + path
			
		try:
			f = self.client.get_file(template_path).read()
		except dropbox.rest.ErrorResponse as e:
			if e.status == 404:
				raise jinja2.TemplateNotFound(template_path)
			else:
				raise IOError("Error connecting to dropbox to download template")
			
		return f,template_path,True
		
def render_dropbox_template(client,template_path,data):
	
	search_root,path = template_path.rsplit('/',1)
	search_root += '/'
	
	env = jinja2.Environment(loader=DropboxLoader(client,search_root))
	
	try:
		template = env.get_template(path)
		output = template.render(**data)
	except jinja2.TemplateNotFound as e:
		raise TemplateNotFound()
	
	return output