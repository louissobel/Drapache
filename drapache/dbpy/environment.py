import builtins.dbpy
import sys

class DBPYModule:
	
	pass


class DBPYEnvironment:
	
	DBPY_TIMEOUT = 25
	BACKGROUND_THREAD_LIMIT = 10
	
	
	def __init__(self,**kwargs):
		
		for k,v in kwargs.items():
			setattr(self,k,v)
		
		self.request_folder = self.request.folder
		self.get_params = self.request.get_params or {}
		self.post_params = self.request.post_params or {}
		
		
		#things that will be global to the builtins
		self.globals = {}
		
		#environment state stuff
		self.modules = {}
		self.cleanups = []
		
		self.background_thread_count = 0
		
		self.in_sandbox = True
		
		
		def register(target):
						
			def decorator(function):
				setattr(target,function.func_name,function)
				return function
			return decorator
		register(self)(register)
		
		@register(self)	
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
						if self.in_sandbox:
							for p in reversed(self.sandbox.protections):
								if p.__class__.__name__ == 'CleanupBuiltins':
									p.frame = sys._getframe()
								p.disable(self.sandbox)
							unrolled = True
							self.in_sandbox = False

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
								for p in self.sandbox.protections:
									p.enable(self.sandbox)
							enable_protections()
							self.in_sandbox = True

					return retval

				#hack to make privileged functions compatible with register
				outer_wrapper.func_name = function.func_name
				outer_wrapper.__doc__ = function.__doc__
				
				return outer_wrapper

		@register(self)
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

				#hack to make privileged functions compatible with register, and docs
				outer_wrapper.func_name = function.func_name
				outer_wrapper.__doc__ = function.__doc__
				return outer_wrapper

			return outer_decorator
			
		#filling builtins with self
		self.globals['dbpy'] = builtins.dbpy.build(self,None)
	
	def add_module(self,mod,name):
		self.modules[name] = mod
		
	def get_module(self,name):
		return self.modules[name]
	
	def get_new_module(self,path):
		new_module = DBPYModule()
		self.add_module(new_module,path)
		return new_module
		
	def add_cleanup(self,function):
		self.cleanups.append(function)
