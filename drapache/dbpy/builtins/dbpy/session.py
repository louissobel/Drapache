

name = 'session'

__doc__ = "A dictionary that represents the session of a user on the site"

class DBPYSession(dict):
	
	def __init__(self,env):
		
		session = env.session
		
		@env.register(self)
		@env.privileged
		def start():
			"""
			Starts the session.
			"""
			session.start()
			self.update(session.inner_dict)
		
		@env.register(self)
		@env.privileged	
		def destroy():
			"""
			Destroys the session
			"""
			session.destroy()
			

def build(env,path):

	
	self = DBPYSession(env)
	env.add_module(self,path+'.'+name)
	
	#adding a cleanup operation
	def finish_session():
		
		if not env.session.is_destroyed:
			env.session.inner_dict.update(self)	
		
		session_header = env.session.get_header()
		if session_header:
			env.response.set_header(*env.session.get_header())
	
	env.add_cleanup(finish_session)		
	
	return self
