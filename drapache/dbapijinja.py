"""
The class that allows templateing from dropbox
"""
import jinja2
import os
import dropbox

class DropboxLoader(jinja2.BaseLoader):
	
	
	def __init__(self,client,search_root):
		self.client = client
		self.search_root = search_root
		
		
	def get_source(self,environment,template):
		
		template_path = os.path.join(self.search_root,template)
		
		try:
			f = self.client.get_file(template_path).read()
		except dropbox.rest.ErrorResponse as e:
			raise jinja2.TemplateNotFound(template)
			
		return f,template_path,True
		
		
def render_dropbox_template(client,template,data,search_root):
	env = jinja2.Environment(loader=DropboxLoader(client,search_root))
	
	try:
		template = env.get_template(template)
		output = template.render(**data)
	except jinja2.TemplateNotFound as e:
		output = "Template %s not found; looking in %s" % (template,search_root)
	
	return output