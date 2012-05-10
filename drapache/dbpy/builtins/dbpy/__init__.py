import templates
import io
import session
import http
import text
import dropbox_dbpy

submodules = [http,io,templates,session,text,dropbox_dbpy]

import os
import imp

name = 'dbpy'

__doc__ = """The root module. All other modules are under this namespace"""

def build(env,path):

	from drapache import dbpy
	
	#assign submodules
	self = env.get_new_module(name)
		
	for module in submodules:
		setattr(self,module.name,module.build(env,name))
	
	
	#get a version of any builtins we use in this module
	io = env.get_module('dbpy.io')
	
	#### write the builtins!
	def dropbox_import_callback(imports):
		#hm... unfortunately, if any of the imports mutate the built_in_hash, they can
		#affect everyones builtins
		#so should I recursively create a new one for each for each?
		#thats the reasoning behind it. I'd love if I didn't have to
		for module_string,module in imports:
			exec module_string in env.globals,module.__dict__
	
	@env.register(self)
	@env.privileged_with_callback(dropbox_import_callback)
	def dropbox_import(*module_paths):
		"""
		Accepts multiple path arguments, and will download each one
		and create a module in the global namespace, like the python import statement
		"""
		#look first in the path given by folder search
		#then look in a '/_scripts' folder? or similarly named?
		#not right now
		
		#NO PACKAGE SUPPORT... SIMPLE FILES ONLY FOR NOW
		imports = []
		for module_path in module_paths:	
			filestring = io.file.read(module_path)
			module_name = os.path.basename(module_path).split('.',1)[0]
			if not module_name in env.globals:
				out_module = imp.new_module(module_name)
				env.globals[module_name] = out_module
				imports.append( (filestring,out_module) )
		
		return imports
		
	@env.register(self)	
	def die(message="",report=True):
		"""
		Terminates the script at the point when it is called, printing the error message if report is True
		"""
		if report:
			print message
		raise dbpy.builtins.UserDieException(message)
		
		
	return self