import dropbox

from drapache import dbapi


name = 'file'

def build(env,path):
	
	self = env.get_new_module(path+'.'+name)
	
	
	@env.register(self)
	@env.privileged
	def _get_lock(path,timeout):
		try:
			file_exists = env.locker.lock(path,timeout)
		except IOError as e:
			#then I wasn't able to lock
			raise IOError("Timeout waiting to open %s for writing or appending'%path")
			
		return file_exists

	@env.register(self)
	@env.privileged
	def _release_lock(path):
		#throws an IOError if it doesn't work
		env.locker.release(path)
	
	@env.register(self)
	@env.privileged
	def open(path,to='read',timeout=None,allow_download=True):
		"""
		loads a file from the users dropbox and returns a string with the contents
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
				
			#register the open file with the locker
			def close_file_cleanup():
				out_file._close(env.locker)
			env.add_cleanup(close_file_cleanup)
					
		else:
			raise TypeError('Invalid mode for opening file. read, write, or append')
			
		return out_file
		
		
	@env.register(self)
	@env.privileged
	def close(file_handle):
		file_handle._close(env.locker)
		
		
	@env.register(self)
	def write(path,string,timeout=None):
		text_file = open(path,to='write',timeout=timeout,allow_download=False)
		text_file.write(string)
		close(text_file)
		
	@env.register(self)
	def read(path):
		return open(path).read()
	
	
	@env.register(self)
	@env.privileged
	def delete(path):

		if not path.startswith('/'):
			path = env.request_folder + path

		try:
			env.client.file_delete(path)
		except dropbox.rest.ErrorResponse:
			raise IOError("Unable to delete file %s"%path)
			
			
	return self