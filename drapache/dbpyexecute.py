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
	
	
	