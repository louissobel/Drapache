"""
Here are the functions that will ship with python executable code
"""

import dbapijinja
import dbapiio

import sys
import imp
import signal
import time
from time import strptime
import pprint

import uuid
import re

import dropbox

import os.path

import markdown
	
import StringIO

from functools import wraps

#### for some reason, we need to preload strptime.
#### this is a weird bug
#### without this block, I was getting "cannot unmarshal code objects in restricted execution mode"
try:
	time.strptime('dfdf')
except:
	pass
	



def get_builtins(**kwargs):
	"""
	client is the client
	get_params are the params from the get request
	sandbox is the sandbox in which it runs
	"""
	
	client = kwargs['client']
	locker = kwargs['locker']

	
	request = kwargs['request']
	response = kwargs['response']
	get_params = request.get_params or {}
	request_folder = request.folder
	
	session = kwargs['session']
	
	sandbox = kwargs['sandbox']

	
	built_in_hash = {'GETPARAMS':get_params,'SESSION':None}
	def register(function):


		def outer_wrapper(*args,**kwargs):
            
			retval = None


			
			try:
				#before I disable protections and restore privileged builtins,
				#i need to change the frame that I am acting on to the current one
				#instead of whatever frame enable was called in
				#find the builrin protection and set its frame
				for p in reversed(sandbox.protections):
					if p.__class__.__name__ == 'CleanupBuiltins':
						p.frame = sys._getframe()
					p.disable(sandbox)
			
				sys.stderr.write('RIGHTHERE'+str(open)+'\n')
				retval = function(*args,**kwargs)
			
			
			finally:
		        #redo the protection
				sys.stderr.write('rolling with modules:%s\n'%str(len(sys.modules)))
				
				#enable for the builtin protection grabs the frame 2 up from enable
				#i want it to enable the protections with outer_wrapper, which is now privileged
				#this ensures that privileged builtins are restored in the next disable
				#so instead of this acting the register frame, I wrap it in a function
				#so it acts on outer_wrapper
				def enable_protections():
					for p in sandbox.protections:
						p.enable(sandbox)
				enable_protections()
				
			return retval
		
		
		built_in_hash[function.func_name] = outer_wrapper
		return function
		
	def register2():
		
		def reg(function):
			register(function)
			bar = built_in_hash[function.func_name]
			def doit():
				bar()
			built_in_hash[function.func_name] = doit
			return doit
		
		return reg
			
	
	def register_with_postop(postop):
		
		#postop will happen in a protected environment again
		
		def register2(function):
			
			def outer_wrapper(*args,**kwargs):

				retval = None
				exception_occured = False
				try:
					old_modules = sandbox.protections[1].modules_dict
					old_builtins = sandbox.protections[1].builtin_dict
					for p in reversed(sandbox.protections):
						p.disable(sandbox)

					retval = function(*args,**kwargs)
					
					sys.stderr.write('just called function itself\n')
					
				finally:
			        #redo the protection
					sys.stderr.write('unrolling (postop) with modules:%s\n'%str(len(sys.modules)))
					for p in sandbox.protections:
						p.enable(sandbox)
				
				#we only get here if there isn't an exception
				return postop(retval)
				
				
			
			built_in_hash[function.func_name] = outer_wrapper
			
			return function
		
		return register2
			
				
		
		
	@register
	def render_template(path,with_data=None,search_root="/_templates"):
		"""
		renders the given template
		"""
		print render_template_to_string(path,with_data,search_root)
		
	@register
	def render_template_to_string(path,with_data=None,search_root="/_templates"):
		"""
		Renders the template like render_template, but returns it as a a string instead
		of printing it.
		"""
		return dbapijinja.render_dropbox_template(client,path,with_data,search_root)
		
	@register
	def _get_lock(path,timeout):
		try:
			file_exists = locker.lock(path,timeout)
		except IOError as e:
			#then I wasn't able to lock
			raise IOError("Timeout waiting to open %s for writing or appending'%path")
			
		return file_exists
			
	@register
	def _release_lock(path):
		
		#throws an IOError if it doesn't work
		locker.release(path)
	
	@register
	def open_file(path,to='read',timeout=None,allow_download=True):
		"""
		loads a file from the users dropbox and returns a string with the contents
		"""
		#if path starts with /, it is absolute.
		#otherwise, it is relative to the request path
		if not path.startswith('/'):
			path = request_folder + path
				
		if to == 'read':
			try:
				out_file = dbapiio.ReadableDropboxFile(path,client)
			except IOError:
				raise IOError('unable to open file %s for reading'%path)
			
		elif to == 'write' or to == 'append' or to == 'json':
			
			#this throws an IOError if it doesn't work
			file_exists = _get_lock(path,timeout)
			
			#I have the lock at this point
			#only download the file if it exists and allow_download is set to true
			#this allows a forced overwrite by setting allow_download to false
			download = file_exists and allow_download
			try:
				if to == 'json':
					out_file = dbapiio.JSONDropboxFile(path,client,download=download)
				else:
					out_file = dbapiio.WritableDropboxFile(path,client,download=download,mode=to)
			except IOError as e:
				raise IOError('Unable to open file for writing ')
				
			#register the open file with the locker
			locker.register_open_file(out_file)
					
		else:
			raise TypeError('Invalid mode for opening file. read, write, or append')
			
		return out_file
		
	@register
	def open_json(path,from_data=None,timeout=None,default=dict):
		#opens up a json file handle of sorts
		#it will be backed by a WritableDropboxFile
		
		out_json = None	
		try:
			if from_data is None:
				json_file = open_file(path,to='json',timeout=timeout) 
				out_json = json_file.json_object
			else:
				json_file = open_file(path,to='json',timeout=Timeout,allow_download=False)
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
		
	@register
	def open_json_list(path,from_data=None,timeout=None):
		out =  open_json(path,from_data=from_data,timeout=timeout,default=list)
		if not isinstance(out,list):
			raise ValueError("Object opened by open_json_list is not a list!")
			
	@register
	def save_json(path,json_object,timeout=None):
		json_file = open_file(path,to='json',timeout=timeout,allow_download=False)
		json_file.json_object = json_object
		json_file.close(loader)
		
	@register
	def write_file(path,string,timeout=None):
		text_file = open_file(path,to='write',timeout=timeout,allow_download=False)
		text_file.write(string)
		text_file.close(loader)
	
	@register
	def read_file(path):
		return open_file(path).read()
		
	@register
	def load_json(path):
		"""
		loads a json file and returns it
		throws a ValueError if the json file fucks up
		"""
		try:
			return json.load(open_file(path))
		except ValueError:
			raise ValueError('Unable to parse json file')		
		
	@register
	def start_session():
		session.start()
		built_in_hash['SESSION'] = session.inner_dict
		
	@register
	def destroy_session():
		session.destroy()
		
	@register
	def set_response_header(key,value):
		response.set_header(key,value)
	
	@register
	def set_response_status(status):
		response.status = status
		
	@register
	def redirect(where,immediately=True):
		set_response_status(302)
		set_response_header('Location',where)
		
		if immediately:
			die("redirecting")
			
			
	@register
	def markdown_to_html(markdown_string):
		return markdown.markdown(markdown_string)
		
	@register
	def pretty_print(thingy,pre=True):
		"""
		Pretty prints the given thingy
		"""
		print "<pre>"
		printer = pprint.PrettyPrinter(indent=4)
		printer.pprint(thingy)
		print "</pre>"
		
	
	
	def dropbox_import_postop(imports):
		#hm... unfortunately, if any of the imports mutate builtins, then they call suffer
		#so should I call it for each?
		#thats the reasoning behind it. I'd love if I didn't have to
		for module_string,module in imports:
			builtins = get_builtins(**kwargs)
			exec module_string in builtins,module.__dict__
	
	
	@register_with_postop(dropbox_import_postop)
	def dropbox_import(*module_paths):
		#look first in the path given by folder search
		#then look in a '/_scripts' folder? or similarly named?
		#not right now
		
		#NO PACKAGE SUPPORT... SIMPLE FILES ONLY
		items = []
		for module_path in module_paths:
			filestring = read_file(module_path)
			module_name = os.path.basename(module_path).split('.',1)[0]
			sys.stderr.write('making module iwth name %s\n'%module_name)
			out_module = imp.new_module(module_name)
			built_in_hash[module_name] = out_module
			items.append( (filestring,out_module) )
		
		return items
		
	    
	    
	@register
	def die(message=""):
		"""
		Raises an Exception
		"""
		raise Exception(message)
		
	
	
	return built_in_hash


	



		
		
		
		
		
		
	