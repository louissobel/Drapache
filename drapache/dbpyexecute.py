"""
responsible for executing downloaded code
"""

import StringIO
import sys
import traceback


import threading
import ctypes
import trace

import __builtin__

import multiprocessing

import sessions

import sandbox as pysandbox
from util import ResponseObject
import dbpybuiltins

import dbapiio

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
	
	def __init__(self,sandbox,builtins,locker,session,response,code,timeout):
		KThread.__init__(self)
		self.sandbox = sandbox
		self.builtins = builtins
		self.locker = locker
		self.session = session
		self.response = response
		self.code = code
		self.timeout = timeout
		self.error = None
		self.error_traceback = ""
		
	def run(self):
		
		traceback.print_stack()
		
		try:
			
			#enable for the builtin protection grabs the frame 2 up from enable
			#i want it to enable the protections with outer_wrapper, which is now privileged
			#this ensures that privileged builtins are restored in the next disable
			#so instead of this acting the register frame, I wrap it in a function
			#so it acts on outer_wrapper
			def enable_protections():
				for protection in self.sandbox.protections:
					protection.enable(self.sandbox)
			enable_protections()


			exec self.code in self.builtins
		
		except Exception as e:			
			self.error = e
			
		finally:
			
			#before I disable protections and restore privileged builtins,
			#i need to change the frame that I am acting on to the current one
			#instead of whatever frame enable was called in
			#find the builrin protection and set its frame
			for protection in reversed(self.sandbox.protections):
				if protection.__class__.__name__ == 'CleanupBuiltins':
					protection.frame = sys._getframe()
				protection.disable(self.sandbox)
			
			sys.stderr.write('unrolled %d many modules\n'%len(sys.modules))
			

			
			t = memoryview('curl')
			sys.stderr.write("here, the error is %s\n"%(str(self.error)))
			
			builtins_set = set(__builtins__.keys())
			frame_set = set(sys._getframe().f_builtins.keys())
			
			difference = builtins_set ^ frame_set
			
			sys.stderr.write('the difference\n%s\n'%str(difference))
			
			sys.stderr.write("FLIJL"+str(__builtins__)+'\n')
			sys.stderr.write(str(len(sys._getframe().f_builtins)))
			
			sys.stderr.write('climbing up the frames:\n')
			
			ok = True
			level = 0
			while ok:
				try:
					f = sys._getframe(level)
					sys.stderr.write('%d\n'%len(f.f_builtins.keys()))
				except ValueError:
					ok = False
				level += 1
			
			#finishing up
			try:
				self.locker.close_all()

				session_header = self.session.get_header()
				if session_header:
					self.response.set_header(*self.session.get_header())

			except Exception as e:
				#an issue releasing resources
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
	
	
	sandbox_config.timeout = None
	

	sandbox = pysandbox.Sandbox(sandbox_config)
	return sandbox		
		

def execute(filestring,**kwargs):
	
	
	PRINT_EXCEPTIONS = True
	EXEC_TIMEOUT = 15
	DEBUG = True
	
	response = ResponseObject(None,"")
	
	sandbox = get_sandbox()
	
	
	locker = dbapiio.DropboxFileLocker(kwargs['client'])
	
	request = kwargs['request']
	

	cookie = request.headers.get('Cookie',None)
	
	session = sessions.DrapacheSession(cookie)
	
	builtin_params = dict(
							response=response,
							locker=locker,
							sandbox=sandbox,
							session=session,
							**kwargs
							)
							
	builtin_dict = dbpybuiltins.get_builtins(**builtin_params)
	
	old_stdout = sys.stdout
	new_stdout = StringIO.StringIO()
	
	sys.stdout = new_stdout
	
	try:
		#im passing things to my sandbox in raw...
		#sandbox._call(pysandbox.sandbox_class._call_exec, (filestring,builtin_dict,None),{})

		#trying the kill here
		sandbox_thread = DBPYExecThread(sandbox,builtin_dict,locker,session,response,filestring,EXEC_TIMEOUT)
		sandbox_thread.start()
	
		tid = sandbox_thread.ident
	
		sandbox_thread.join(EXEC_TIMEOUT)
	
		if sandbox_thread.isAlive():
			#time to kill it
			#for protection in reversed(sandbox.protections):
			#	protection.disable(sandbox)
		
			sandbox_thread.kill()
			sandbox_thread.join()
		
		if sandbox_thread.error is not None:
			
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
		
	response.set_header('Content-Type','text/html')
	
	return response
	



def bug_reproduce_builtins(sandbox):
	
	built_in_hash = {}
	
	def register(function):


		def outer_wrapper(*args,**kwargs):
            
			retval = None
			try:
			    for p in reversed(sandbox.protections):
				    p.disable(sandbox)
			
			    retval = function(*args,**kwargs)
			
			
			finally:
		        #redo the protection
				for p in sandbox.protections:
					p.enable(sandbox)
				
			return retval
		
		
		built_in_hash[function.func_name] = outer_wrapper
		return function
		
	def register2():

		def reg(function):
			register(function)
			bar = built_in_hash[function.func_name]
			def doit():
				bar()
			built_in_hash[function.func_name] = doit
			return doit

		return reg
		
		
	@register2()
	def foo():
		sys.stderr.write('LALALA\n')
		traceback.print_stack()
		if __name__ == '__main__':
			sys.stderr.write('main\n')
		sys.stderr.write('hey there!\n')
		
	return built_in_hash
	
class BugThread(threading.Thread):
	
	def __init__(self,sandbox,string,builtins):
		threading.Thread.__init__(self)
		self.sandbox = sandbox
		self.string = string
		self.builtins = builtins
		
		
	def run(self):
		
		try:
			#manually turning on the sandbox protections
			for protection in self.sandbox.protections:
				protection.enable(self.sandbox)
				
			exec self.code in self.builtins
		
		except Exception as e:			
			self.error = e
			
		finally:
			for protection in reversed(self.sandbox.protections):
				protection.disable(self.sandbox)
		
		
		
		
		
def bug_reproduce():
	
	sandbox = get_sandbox()
	
	
	t = BugThread(sandbox,"foo()",bug_reproduce_builtins(sandbox))
	t.start()
			
	sys.stderr.write('builtin count:%d\n'%len(__builtins__.__dict__))
	sys.stderr.write('framebuiltin count:%d\n'%len(sys._getframe().f_builtins))
		
	
if __name__ == "__main__":
	bug_reproduce()