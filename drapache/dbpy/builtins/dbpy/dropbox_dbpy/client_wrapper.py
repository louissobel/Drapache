
name = 'api'

__doc__ = "Access to the raw dropbox API methods"




WRAPPED_METHODS = [
	'account_info',
	'add_copy_ref',
	'create_copy_ref',
	'delta',
	'file_copy',
	'file_create_folder',
	'file_delete',
	'file_move',
	'get_file',
	'get_file_and_metadata',
	'media',
	'metadata',
	'put_file',
	'request',
	'restore',
	'revisions',
	'search',
	'share',
	'thumbnail',
	'thumbnail_and_metadata',
	]
	
def get_doc():

	import dropbox
	import inspect

	children = []
	out_hash = {'type':'module','name':name,'children':children,'doc':__doc__}
	
	for method in WRAPPED_METHODS:
		
		db_function = getattr(dropbox.client.DropboxClient,method)
		
		args, varargs, varkw, defaults = inspect.getargspec(db_function)
		argspec = inspect.formatargspec(args, varargs, varkw, defaults)
		
		new_hash = {'type':'function','name':method+argspec,'children':None,'doc':db_function.__doc__}
	
		children.append(new_hash)
	return out_hash

def build(env,path):
	
	self = env.get_new_module(path+'.'+name)
	
	
	def register_client_method(method_name):
		
		method = getattr(env.proxy.client, method_name)
		
		@env.register(self)
		@env.protected
		def outer_function(*args,**kwargs):
			return method(*args,**kwargs)
		
		