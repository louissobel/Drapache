

name = 'http'

def build(env,path):
	
	self = env.get_new_module(path+'.'+name)
	
	dbpy = env.get_module('dbpy')
	
	@env.register(self)
	def set_response_header(key,value):
		env.response.set_header(key,value)
		
	@env.register(self)
	def get_request_header(key):
		return env.request.headers.get(key)
	
	@env.register(self)
	def set_response_status(status):
		env.response.status = status
		
	@env.register(self)
	def redirect(where,immediately=True):
		set_response_status(302)
		set_response_header('Location',where)
		
		if immediately:
			dbpy.die("redirecting")
			
			
	return self