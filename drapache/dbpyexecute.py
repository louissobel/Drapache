"""
responsible for executing downloaded code
"""

import StringIO
import sys
import traceback


import threading
import ctypes
import trace

import multiprocessing

import sandbox as pysandbox
from util import ResponseObject
import dbpybuiltins

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
	
	def __init__(self,sandbox,builtins,code,timeout):
		KThread.__init__(self)
		self.sandbox = sandbox
		self.builtins = builtins
		self.code = code
		self.timeout = timeout
		self.error = None
		
	def run(self):
		
		try:
			#getting around the sanboxes protections by manually getting to the call
			self.sandbox._call(pysandbox.sandbox_class._call_exec, (self.code,self.builtins,None), {})
			#exec self.code in self.builtins,{}
		
		except Exception as e:
			sys.stderr.write('\nage\n')
			self.error = e
			
class DBPYExecProcess(multiprocessing.Process):
	
	def __init__(self,kwargs,code,timeout):
		multiprocessing.Process.__init__(self)
		self.sandbox = get_sandbox()
		self.builtins = dbpybuiltins.get_builtins(sandbox=self.sandbox,**kwargs)
		self.code = code
		self.timeout = timeout
		self.error = None
		
	def run(self):
		
		try:
			#self.sandbox._call(pysandbox.sandbox_class._call_exec, (self.code,self.builtins,None), {})
			exec self.code in self.builtins,{}
		
		except Exception as e:
			sys.stderr.write('exception in thread')
			self.error = e

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
	
	
	sandbox = get_sandbox()	
	builtin_dict = dbpybuiltins.get_builtins(sandbox=sandbox,**kwargs)
	
	old_stdout = sys.stdout
	new_stdout = StringIO.StringIO()
	
	sys.stdout = new_stdout
	
	try:
		#im passing things to my sandbox in raw...
		#sandbox._call(pysandbox.sandbox_class._call_exec, (filestring,builtin_dict,None),{})

		#trying the kill here
		USE = 'thread'
		
		if USE == 'thread':
			sys.stderr.write("starting run exec thread\n")
			sandbox_thread = DBPYExecThread(sandbox,builtin_dict,filestring,EXEC_TIMEOUT)
			sandbox_thread.start()
		
			tid = sandbox_thread.ident
		
			sandbox_thread.join(EXEC_TIMEOUT)
		
			if sandbox_thread.isAlive():
				#time to kill it
				for protection in reversed(sandbox.protections):
					protection.disable(sandbox)
			
				sandbox_thread.kill()
				sandbox_thread.join()
			
			if sandbox_thread.error is not None:
				raise sandbox_thread.error
					
		elif USE == 'process':
			sys.stderr.write("starting run exec procss\n")
			sandbox_process = DBPYExecProcess(kwargs,filestring,EXEC_TIMEOUT)
			sandbox_process.start()
			
			pid = sandbox_process.pid
			
			sandbox_process.join(EXEC_TIMEOUT)
			
			if sandbox_process.is_alive():
				#time to kill it
				#for protection in reversed(sandbox.protections):
				#	proctection.disable(sandbox)
					
				sandbox_process.terminate()
				sandbox_process.join()
				
				if sandbox_process.error is not Noen:
					raise sandbox_process.error
					
		elif USE == 'single':
			
			exec filestring in builtin_dict,{}

	except:
		if PRINT_EXCEPTIONS:
			print "<pre>"
			traceback.print_exc(file=new_stdout)
			print "</pre>"
	

	sys.stdout = old_stdout
	
	sys.stderr.write("done run exec thread\n")
	sys.stderr.write("donthread: %s"%str(threading.enumerate()))
	return ResponseObject(200,new_stdout.getvalue(),{'Content-type':'text/html'})
	
	
	