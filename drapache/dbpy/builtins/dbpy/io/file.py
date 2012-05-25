import dropbox

from drapache import dbapi

import sys

name = 'file'

__doc__ = "Functions for reading/writing with files that live on dropbox"

def build(env,path):
	
	self = env.get_new_module(path+'.'+name)
	
	dbpy = env.get_module('dbpy')
	
	@env.register(self)
	@env.privileged
	def _get_lock(path,timeout):
		"""
		Internal function, public because, why hide it?
		"""
		try:
			file_exists = env.locker.lock(path,timeout)
		except IOError as e:
			#then I wasn't able to lock
			raise IOError("Timeout waiting to open %s for writing or appending'%path")
			
		return file_exists

	@env.register(self)
	@env.privileged
	def _release_lock(path):
		"""
		Internal function, public because, why hide it?
		"""
		#throws an IOError if it doesn't work
		env.locker.release(path)
	
	@env.register(self)
	@env.privileged
	def open(path,to='read',timeout=None,allow_download=True):
		"""
		Opens a file on your dropbox.
		There are three modes: read, write, append, and json. If the mode is read, the file is simply
		downloaded and a file-like (StringIO) object is returned. If the mode is write, append or json
		the function will try for `timeout` seconds to obtain a lock for the given path. If it fails,
		it will raise an `IOError`. Otherwise, it will then download the file and return either
		a file-like filehandle (in the case of write mode) or a json dictionary handle that will update
		back to the dropbox file (in the case of json mode).
		
		If the mode is append, all writes will start at the end. If the mode is write, all writes will overwrite
		the data starting at the start of the file.
		
		"""
		#if path starts with /, it is absolute.
		#otherwise, it is relative to the request path
		if not path.startswith('/'):
			path = env.request_folder + path
				
		if to == 'read':
			try:
				out_file = dbapi.io.ReadableDropboxFile(path,env.client)
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
					out_file = dbapi.io.JSONDropboxFile(path,env.client,download=download)
				else:
					out_file = dbapi.io.WritableDropboxFile(path,env.client,download=download,mode=to)
			except IOError as e:
				raise IOError('Unable to open file for writing ')
				
			#register the open file with the locker,
			#and the necessary cleanup action
			def close_file_cleanup():
				out_file._close(env.locker)
			env.add_cleanup(close_file_cleanup)
			
			env.locker.register_open_file(out_file)
					
		else:
			raise TypeError('Invalid mode for opening file. read, write, or append')
			
		return out_file
		
		
	@env.register(self)
	@env.privileged
	def close(file_handle):
		"""
		Closes the given file handle. This will happen automatically,
		but do this to release resources (it releases the lock too)
		"""
		file_handle._close(env.locker)
		
		
	@env.register(self)
	def write(path,string,timeout=None):
		"""
		Writes the given string to the path given by `path`
		"""
		text_file = open(path,to='write',timeout=timeout,allow_download=False)
		text_file.write(string)
		close(text_file)
		
	@env.register(self)
	def read(path):
		"""
		reads the file given by path and returns a string of its contents
		"""
		return open(path).read()
		
	
	@env.register(self)
	def render(path):
		"""
		Will read and print the file given by path, withthe proper content type
		"""
		file_h = open(path)
		content_type = file_h.metadata['mime_type']
		dbpy.http.set_response_header('Content-Type',content_type)
		sys.stdout.write(file_h.read())
		
	
			
			
	return self