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
import json
	
import StringIO

from functools import wraps

class UserDieException(Exception):
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
	post_params = request.post_params or {}
	
	request_folder = request.folder
	
	session = kwargs['session']
	
	sandbox = kwargs['sandbox']

	#goo... but i need state that is mutable 
	#by any privileged function... this dict becomes visible to all privileged
	#function. this allows the nesting of privilegeds
	in_sandbox = {'is':True}
	
	
	built_in_hash = {'GETPARAMS':get_params,'POSTPARAMS':post_params,'SESSION':None}
		
	
	def register(function):
		built_in_hash[function.func_name] = function
		return function
		
	def privileged(function):
		"""
		A decorator that replaces the given function with 
		one that first takes the current frame out of the sandbox
		and then executes the function, finally replaces the protections of the sandbox
		
		There are some hacks that cater to the way that pysandbox (which is awesome) was written
		
		And a dictionary was defined (in_sandbox) at the same scope os the function itself... this acts as
		a global flag whether or not sandbox is currently enabled. This allows the nesting of privileged functions
		"""
		def outer_wrapper(*args,**kwargs):
            
			retval = None
			
			unrolled = False
			
			try:
				#before I disable protections and restore privileged builtins,
				#i need to change the frame that I am acting on to the current one
				#instead of whatever frame enable was called in
				#find the builtin protection and set its frame
				if in_sandbox['is']:
					for p in reversed(sandbox.protections):
						if p.__class__.__name__ == 'CleanupBuiltins':
							p.frame = sys._getframe()
						p.disable(sandbox)
					unrolled = True
					in_sandbox['is'] = False
			
				retval = function(*args,**kwargs)
			
			
			finally:
		        #redo the protection
				
				#enable for the builtin protection grabs the frame 2 up from enable
				#i want it to enable the protections in the outer_wrapper frame, which is now privileged
				#this ensures that privileged builtins are restored in the next disable
				#so instead of this acting on the 'privileged' frame, I wrap it in a function
				#to push it one place lower in the stack frame so it acts on outer_wrapper
				if unrolled:
					def enable_protections():
						for p in sandbox.protections:
							p.enable(sandbox)
					enable_protections()
					in_sandbox['is'] = True
				
			return retval
		
		#hack to make privileged functions compatible with register
		outer_wrapper.func_name = function.func_name
		return outer_wrapper
			
	
	def privileged_with_callback(callback,before=False):
		"""
		A decorator factory that returns a decorator that wraps the function
		by privileging it, and composing it with the unprivileged callback
		
		if before is True (false by default) the callback function will actually get executed *before* the privileged one
		"""
		
		def outer_decorator(function):
			
			function_p = privileged(function)
			
			if before:
				def outer_wrapper(*args,**kwargs):
					return function_p(callback(*args,**kwargs))
			else:
				def outer_wrapper(*args,**kwargs):
					return callback(function_p(*args,**kwargs))

			#hack to make privileged functions compatible with register
			outer_wrapper.func_name = function.func_name
			return outer_wrapper
		
		return outer_decorator
			
				
		
	####### Template stuff
	@privileged
	def _render_template_to_string(path,with_data):
		return dbapijinja.render_dropbox_template(client,path,with_data)
	
	@register
	def render_template(path,with_data=None,search_root="/_templates"):
		"""
		renders the given template
		"""
		print render_template_to_string(path,with_data)
		
	@register
	def render_template_to_string(path,with_data=None):
		"""
		Renders the template like render_template, but returns it as a a string instead
		of printing it.
		"""
		
		search_hierarchy = [request_folder,request_folder+'_templates/','/_templates/']
		
		if path.startswith('/'):
			return _render_template_to_string(path,with_data)
		
		else:
			for prefix in search_hierarchy:
				check_path = prefix + path
				try:
					return _render_template_to_string(check_path,with_data)
				except dbapijinja.TemplateNotFound:
					pass
			raise dbapijinja.TemplateNotFound()
		
	
	################### file io stuff
	@register
	@privileged
	def _get_lock(path,timeout):
		try:
			file_exists = locker.lock(path,timeout)
		except IOError as e:
			#then I wasn't able to lock
			raise IOError("Timeout waiting to open %s for writing or appending'%path")
			
		return file_exists

	@register
	@privileged
	def _release_lock(path):
		
		#throws an IOError if it doesn't work
		locker.release(path)
	
	@register
	@privileged
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
	@privileged
	def close_file(file_handle):
		file_handle._close(locker)
		
	@register
	@privileged
	def close_json(inner_dict):
		for open_file_h in locker.open_files:
			if hasattr(open_file_h,'json_object'):
				if open_file_h.json_object is inner_dict:
					open_file_h._close(locker)
		
	@register
	@privileged
	def save_json(path,json_object,timeout=None):
		json_file = open_file(path,to='json',timeout=timeout,allow_download=False)
		json_file.json_object = json_object
		close_file(json_file)
		
	@register
	def write_file(path,string,timeout=None):
		text_file = open_file(path,to='write',timeout=timeout,allow_download=False)
		text_file.write(string)
		close_file(text_file)
	
	@register
	def read_file(path):
		return open_file(path).read()
		
	@register
	@privileged
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
	@privileged
	def delete_file(path):
		
		if not path.startswith('/'):
			path = request_folder + path
			
		try:
			client.file_delete(path)
		except dropbox.rest.ErrorResponse:
			raise IOError("Unable to delete file %s"%path)
		
	
	############ session stuff
	@register
	@privileged
	def start_session():
		session.start()
		built_in_hash['SESSION'] = session.inner_dict
		
	@register
	@privileged
	def destroy_session():
		session.destroy()
		
		
	########## http stuff
	@register
	def set_response_header(key,value):
		response.set_header(key,value)
		
	@register
	def get_request_header(key):
		return request.headers.get(key)
	
	@register
	def set_response_status(status):
		response.status = status
		
	@register
	def redirect(where,immediately=True):
		set_response_status(302)
		set_response_header('Location',where)
		
		if immediately:
			die("redirecting")
			
	
	############ text stuff	
	@register
	@privileged
	def markdown_to_html(markdown_string):
		return markdown.markdown(markdown_string)
		
	@register
	@privileged
	def pretty_print(thingy,pre=True):
		"""
		Pretty prints the given thingy
		"""
		print "<pre>"
		printer = pprint.PrettyPrinter(indent=4)
		printer.pprint(thingy)
		print "</pre>"
		
	
	############ import stuff
	
	def dropbox_import_callback(imports):
		#hm... unfortunately, if any of the imports mutate the built_in_hash, they can
		#affect everyones builtins
		#so should I recursively create a new one for each for each?
		#thats the reasoning behind it. I'd love if I didn't have to
		for module_string,module in imports:
			builtins = get_builtins(**kwargs)
			exec module_string in builtins,module.__dict__
	
	@register
	@privileged_with_callback(dropbox_import_callback)
	def dropbox_import(*module_paths):
		#look first in the path given by folder search
		#then look in a '/_scripts' folder? or similarly named?
		#not right now
		
		#NO PACKAGE SUPPORT... SIMPLE FILES ONLY FOR NOW
		imports = []
		for module_path in module_paths:
			filestring = read_file(module_path)
			module_name = os.path.basename(module_path).split('.',1)[0]
			out_module = imp.new_module(module_name)
			built_in_hash[module_name] = out_module
			imports.append( (filestring,out_module) )
		
		return imports
		
	    
	##### other stuff
	@register
	def die(message="",report=True):
		"""
		Raises an Exception
		"""
		if report:
			print message
		raise UserDieException(message)
		
	
	
	return built_in_hash


	



		
		
		
		
		
		
	