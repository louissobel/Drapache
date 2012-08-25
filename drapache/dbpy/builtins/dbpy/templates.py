#big imports
from drapache import dbapi

import sys

name = 'templates'

__doc__ = "Functions for using jinja templates hosted on dropbox"

def build(env,path):
	
	self = env.get_new_module(path+'.'+name)
	
	#no submodules
	
	@env.privileged
	def _render_template_to_string(path, with_data):
		return dbapi.jinja.render_dropbox_template(env.proxy.client, path, with_data)
	
	@env.register(self)
	def render(path,with_data=None):
		"""
		Renders the jinja template found in `path`. The parameter `with_data` (None by default)
		specifies a dictionary that will be used to fill in the template.
		"""
		print render_to_string(path,with_data)
		
	@env.register(self)
	def render_to_string(path, with_data=None):
		"""
		Renders the template like render_template, but returns it as a a string instead
		of printing it.
		"""
		
		search_hierarchy = [env.request_folder,env.request_folder+'_templates/','/_templates/']
		
		if path.startswith('/'):
			return _render_template_to_string(path,with_data)
		
		else:
			sys.stderr.write(str(_render_template_to_string)+"\n")
			for prefix in search_hierarchy:
				check_path = prefix + path
				try:
					return _render_template_to_string(check_path,with_data)
				except dbapi.jinja.TemplateNotFound:
					pass
			raise dbapi.jinja.TemplateNotFound()
			
	return self