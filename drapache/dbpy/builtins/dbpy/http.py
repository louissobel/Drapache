

name = 'http'

__doc__ = "The http module provides access to methods concerning the http request and response"

def build(env,path):
	
	self = env.get_new_module(path+'.'+name)
	
	dbpy = env.get_module('dbpy')
	
	
	#TODO:
	#look... all this duplication of data in the request.
	#eh.
	
	#DOC:get_params
	"""
	The parsed parameters from the request url in a multidict
	"""
	self.get_params = env.get_params
	
	#DOC:post_params
	"""
	If the request was a post request, the parsed parameters from the body of the post
	"""
	self.post_params = env.post_params
	
	#DOC:request
	"""
	The raw request object.
	"""
	self.request = env.request
	
	
	@env.register(self)
	def set_response_header(header,value):
		"""
		Sets the header `header` to the value given by `value`
		"""
		env.response.set_header(header,value)
		
	@env.register(self)
	def get_request_header(header):
		"""
		Returns the header specified by `header`
		"""
		return env.request.headers.get(header)
	
	@env.register(self)
	def set_response_status(status):
		"""
		Sets the HTTP Status code of the response to `status`
		"""
		env.response.status = status
		
	@env.register(self)
	def redirect(where,immediately=True,status=302):
		"""
		Redirects the HTTP request to another location.
		The target location is given by `where`.
		If immediately is true, the script will exit immediately once this function is executed.
		The status is 302 by default, but could be set to whatever.
		"""
		
		set_response_status(302)
		set_response_header('Location',where)
		if immediately:
			dbpy.die("redirecting")
			
	@env.register(self)
	def error(which,message,immediately=True):
		"""
		Returns an error response
		"""
		env.response.status = which
		env.response.body = message
		env.response.error = True
		if immediately:
			dbpy.die("User Error - %d" % which)
			
			
	return self