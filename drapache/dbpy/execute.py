"""
responsible for executing downloaded code
"""

import StringIO
import sys
import traceback
import threading
import trace

import sandbox as pysandbox

from drapache.util.http import Response
from drapache import dbapi
from drapache import util

import builtins
import environment

class Timeout(Exception):
	pass


class KThread(threading.Thread):
	"""A subclass of threading.Thread, with a kill()
	method.
	found this @ http://www.velocityreviews.com/forums/t330554-kill-a-thread-in-python.html"""
	def __init__(self, *args, **keywords):
			threading.Thread.__init__(self, *args, **keywords)
			self.killed = False
			self.timeout = None

	def start(self):
		"""Start the thread."""
		self.__run_backup = self.run
		self.run = self.__run # Force the Thread to install our trace.
		threading.Thread.start(self)

	def __run(self):
		"""Hacked run function, which installs the
		trace."""
		sys.settrace(self.globaltrace)
		self.__run_backup()
		self.run = self.__run_backup

	def globaltrace(self, frame, why, arg):
		if why == 'call':
			return self.localtrace
		else:
			return None

	def localtrace(self, frame, why, arg):
			if self.killed:
				if why == 'line':
					raise Timeout("DBPY code timed out after %s seconds"%self.timeout)
			return self.localtrace

	def kill(self):
		self.killed = True



class DBPYExecThread(KThread):
	
	def __init__(self,env,code,timeout):
		KThread.__init__(self)
		self.env = env
		self.code = code
		self.timeout = timeout
		self.error = None
		self.error_traceback = ""
		
	def run(self):
		
		try:
			
			#enable for the builtin protection grabs the frame 2 up from enable
			#i want it to enable the protections with outer_wrapper, which is now privileged
			#this ensures that privileged builtins are restored in the next disable
			#so instead of this acting the register frame, I wrap it in a function
			#so it acts on outer_wrapper
			def enable_protections():
				for protection in self.env.sandbox.protections:
					protection.enable(self.env.sandbox)
			enable_protections()


			exec self.code in self.env.globals
		
		except builtins.UserDieException:
			pass
		
		except Exception as e:			
			self.error = e
			
		finally:
			
			#before I disable protections and restore privileged builtins,
			#i need to change the frame that I am acting on to the current one
			#instead of whatever frame enable was called in
			#find the builrin protection and set its frame
			for protection in reversed(self.env.sandbox.protections):
				if protection.__class__.__name__ == 'CleanupBuiltins':
					protection.frame = sys._getframe()
				protection.disable(self.env.sandbox)

			
			#finishing up
			#resource releasing (post-execution actions)
			#are registered here
			try:
				for op in self.env.cleanups:
					op()

			except Exception as e:
				#an issue releasing resources
				#if there is already an error, we do not report it?
				#maybe errors releasing resources should have higher precedence..
				if not self.error:
					self.error = e
				
			if self.error:
				self.error_traceback = traceback.format_exc()


def get_sandbox():
	sandbox_config = pysandbox.SandboxConfig()
	sandbox_config.enable("stdout")
	sandbox_config.enable("time")
	sandbox_config.enable("math")
	sandbox_config.enable("exit")
	sandbox_config.enable("stderr")
	
	sandbox_config.timeout = None
	
	sandbox = pysandbox.Sandbox(sandbox_config)
	return sandbox		
		

def execute(filestring,**kwargs):
	
	
	PRINT_EXCEPTIONS = True
	EXEC_TIMEOUT = 25
	DEBUG = True
	
	response = Response(None,"")
	
	sandbox = get_sandbox()
	
	#setting up the parameters for the builtin construction
	locker = dbapi.io.DropboxFileLocker(kwargs['client'])
	request = kwargs['request']
	
	cookie = request.headers.get('Cookie',None)
	session = util.sessions.DrapacheSession(cookie)
	
	builtin_params = dict(
							response=response,
							locker=locker,
							sandbox=sandbox,
							session=session,
							**kwargs
							)
							
	env = environment.DBPYEnvironment(**builtin_params)
	
	#replaceing stdout
	old_stdout = sys.stdout
	new_stdout = StringIO.StringIO()
	sys.stdout = new_stdout
	
	try:

		sandbox_thread = DBPYExecThread(env,filestring,EXEC_TIMEOUT)
		sandbox_thread.start()
	
		sandbox_thread.join(EXEC_TIMEOUT)
	
		if sandbox_thread.isAlive():
			#time to kill it
		
			sandbox_thread.kill()
			sandbox_thread.join()
		
		if sandbox_thread.error is not None:
			
			#this is where processing of the traceback should take place
			#so that we can show a meaningful error message
			if DEBUG:
				sys.stdout.write(sandbox_thread.error_traceback)

			raise sandbox_thread.error

	except:
		if PRINT_EXCEPTIONS:
			print "<pre>"
			traceback.print_exc(file=new_stdout)
			print "</pre>"
	

	sys.stdout = old_stdout
	response.body = new_stdout.getvalue()

	if response.status is None:
		response.status = 200
	
	if not 'Content-Type' in response.headers:
		response.set_header('Content-Type','text/html')
	
	return response