import dropbox

import client_wrapper


submodules = [client_wrapper]


name = 'dropbox'

__doc__ = "Access to your dropbox"


def build(env, path):
	
	self = env.get_new_module(path+'.'+name)
	
	for module in submodules:
		setattr(self,module.name,module.build(env,path+'.'+name))
		
	client = env.proxy.client
		
	@env.register(self)
	@env.privileged
	def remove(path):
		"""
		deletes the given path.
		"""
		if not path.startswith('/'):
			path = env.request_folder + path

		try:
			client.file_delete(path)
		except dropbox.rest.ErrorResponse:
			raise IOError("Unable to delete file %s"%path)	
	
	@env.register(self)
	@env.privileged
	def list_directory(path=None):
		"""
		gets the contents of the current directory,
		or path if it is given. If path is not a directory, return none
		"""
		
		if path is None:
			path = env.request_folder
		elif not path.startswith('/'):
			path = env.request_folder + path
				
		try:
			
			metadata = client.metadata(path)
			
			if not metadata['is_dir']:
				return None
			
			else:
				try: #wrap in KeyError just in case
					return [file_meta['path'].rsplit('/',1)[1] for file_meta in metadata['contents']]
				except KeyError:
					return None
		except dropbox.rest.ErrorResponse:
			raise IOError("Unable to get directory contents %s" % path)
			
	@env.register(self)
	@env.privileged
	def make_directory(path):
		"""
		Creates a directory at the given path. Path can be relative or absolute.
		Returns the path at which it was created
		"""
		if not path.startswith('/'):
			path = env.request_folder + path
		
		try:
			
			client.file_create_folder(path)
			return path
			
		except dropbox.rest.ErrorResponse:
			raise IOError("Unable to create directory %s" % path)
	
	
	
	return self	
