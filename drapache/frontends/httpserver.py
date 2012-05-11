"""
The http server implementation
"""

import BaseHTTPServer
import SocketServer
import socket #for socket.error
import re
import os
import sys
import urlparse
import traceback
import threading

import drapache
from drapache import util



class DropboxHTTPRequestHandler(BaseHTTPServer.BaseHTTPRequestHandler):
	"""
	This class is responsible for sub-routing and headers,
	getting/processing content gets farmed out (this will help when i thread?)
	also, pulling out parameters
	"""
	
	
	
	
	#def setup(self):
	#	BaseHTTPServer.BaseHTTPRequestHandler.setup(self)
		#print self.request.settimeout(5)
	
	def do_GET(self):
		return self.serve(method='get')
		
	def do_POST(self):
		return self.serve(method='post')
	
	def serve(self,method=None):
			
		try:
			
			#create an empty request object
			request = util.http.Request()

			#pulling out the host
			host_string = self.headers.get("Host")
			host_rest = host_string.split(".",1) #at most one split
			if len(host_rest) == 1:
				subdomain = None
			else:
				subdomain = host_rest[0]
			
			#setting some request variables
			request.host = host_string
			request.subdomain = subdomain
			request.headers = self.headers
		
			#pulling out the request path and query from the url
			path,query_string = self.parse_raw_path(self.path)
		
			#parsing the query
			if query_string is not None:
				get_params = urlparse.parse_qs(query_string)
			else:
				get_params = None
		
			#setting more request variables IMPORTANT. fragile though. sorry
			request.path = path
			request.folder = path.rsplit('/',1)[0] + '/'
			request.get_params = get_params
			request.query_string = query_string
		
			#there must be a subdomain
			if subdomain is None:
				self.send_error(400,"Dropache requires a username as the route")
				return None
			
			
			#getting a subdomain_manager instance
			#the factory function is an attribute of the server
			#to keep it configurable
			subdomain_manager = self.server.get_subdomain_manager()
		
			#looking up the oauth for the given subdomain
			try:
				subdomain_token = subdomain_manager.get_token(subdomain)
				if subdomain_token is None:
					self.send_error(404,"Subdomain %s does not exist"%subdomain)
					return None
			except util.subdomain_managers.SubdomainException as e:
				self.send_error(503,"Error in subdomain lookup:\n"+e.message)
				return None
			
			#getting a dropbox_client
			#the factory function is an attribute of the server
			#to keep it configurable
			subdomain_client = self.server.get_dropbox_client(subdomain_token)
		
		
			#parsing post parameters if it is a post request
			if method == 'post':
				request_length = int(self.headers.get('Content-length',0))
				foo = self.rfile.read(request_length)
				post_params = urlparse.parse_qs(foo)
				request.post_params = post_params
			else:
				request.post_params = None
		
			#getting the response from dropbox
			response = drapache.dbserver.DropboxServer(subdomain_client,request).serve()
			
			if response.error:
				self.send_error(response.status,response.body)
				return None
		
			else:
				self.send_response(response.status)
				for h,v in response.headers.items():
					self.send_header(h,v)
				self.end_headers()
				self.wfile.write(response.body)
				return None
				
		##### Catchall errors
		except socket.error as e:
			#check if it was a broken pipe
			#... assume it was a broken pipe
			#if it was a broken pipe, the client went away. which is fine. and i don't need a traceback for that.
			#nor should i try to send a 500 message, because there is no way it will get through
			pass
			
		
		except Exception as e:
			### Caught an error, now attempting to send a 500 server error response
			sys.stderr.write("WHAT AM I DOING EHRE!!!!!")
			traceback.print_exc()
			self.send_error(500,str(e))
		
		
	def parse_raw_path(self,path):
		"""
		pulls out the user, the path, and the query if any

		"""
		
		#*.drapache:port/<the rest of the path>
		po = urlparse.urlparse(path)
		sub_path = po.path
		query = po.query
		if sub_path == '':
			sub_path = '/'
		if query == '':
			query = None
		
		return sub_path,query
		

class ThreadJoiningForkingMixIn:

	"""
	Mix-in class to handle each request in a new process.
	COPIED FROM STANDARD LIBRARY
	EXCEPT THAT IT WAITS ON ALL BACKGROUND THREADS TO FINISH BEFORE os._exit-ing
	"""

	timeout = 300
	active_children = None
	max_children = 40

	def collect_children(self):
		"""Internal routine to wait for children that have exited."""
		if self.active_children is None: return
		while len(self.active_children) >= self.max_children:
			# XXX: This will wait for any child process, not just ones
			# spawned by this library. This could confuse other
			# libraries that expect to be able to wait for their own
			# children.
			try:
				pid, status = os.waitpid(0, 0)
			except os.error:
				pid = None
			if pid not in self.active_children: continue
			self.active_children.remove(pid)

		# XXX: This loop runs more system calls than it ought
		# to. There should be a way to put the active_children into a
		# process group and then use os.waitpid(-pgid) to wait for any
		# of that set, but I couldn't find a way to allocate pgids
		# that couldn't collide.
		for child in self.active_children:
			try:
				pid, status = os.waitpid(child, os.WNOHANG)
			except os.error:
				pid = None
			if not pid: continue
			try:
				self.active_children.remove(pid)
			except ValueError, e:
				raise ValueError('%s. x=%d and list=%r' % (e.message, pid,
														   self.active_children))

	def handle_timeout(self):
		"""Wait for zombies after self.timeout seconds of inactivity.

		May be extended, do not override.
		"""
		self.collect_children()

	def process_request(self, request, client_address):
		"""Fork a new subprocess to process the request."""
		self.collect_children()
		pid = os.fork()
		if pid:
			# Parent process
			if self.active_children is None:
				self.active_children = []
			self.active_children.append(pid)
			self.close_request(request) #close handle in parent process
			return
		else:
			# Child process.
			# This must never return, hence os._exit()!
			try:
				self.finish_request(request, client_address)
				self.shutdown_request(request)
				
				JOINTHREADS_TIMEOUT = 10 #we will try for ten seconds to wait for background threads to finish
				JOINTHREADS_INCREMENT = .1 #how long we try to join each thread
				
				been_waiting = 0
				while threading.active_count() > 1 and been_waiting < JOINTHREADS_TIMEOUT: #while there are more threads than this one
					for thread in threading.enumerate():
						if not thread is threading.current_thread():
							thread.join(JOINTHREADS_INCREMENT)
							been_waiting += JOINTHREADS_INCREMENT				
				
				#at this point, either all background threads have finished or we've been waiting damn long enough
				os._exit(0)
			except:
				try:
					self.handle_error(request, client_address)
					self.shutdown_request(request)
				finally:
					os._exit(1)
		
class DropboxForkingHTTPServer(ThreadJoiningForkingMixIn,BaseHTTPServer.HTTPServer):
	
	def set_config(self,subdomain_manager_factory,dropbox_client_factory):
		self.get_subdomain_manager = subdomain_manager_factory
		self.get_dropbox_client = dropbox_client_factory
		
	
	#catchall errors
	def finish_request(self,*args,**kwargs):
		try:
			BaseHTTPServer.HTTPServer.finish_request(self,*args,**kwargs)
		except socket.error as e:
			sys.stderr.write("[error] %s\n"%"Client went away")
		except Exception as e:
			traceback.print_exc()
			sys.stderr.write("[error] Uncought response exception: %s\n"%str(e))
			
			
class HttpDrapache:


	def __init__(self):
		self.port = None
		self.subdomain_manager_factory = None
		self.dropbox_client_factory = None

	def start(self):

		assert self.port
		assert self.subdomain_manager_factory
		assert self.dropbox_client_factory


		server_address = ('0.0.0.0',self.port)
		self.httpd = DropboxForkingHTTPServer(server_address,DropboxHTTPRequestHandler)
		self.httpd.set_config(self.subdomain_manager_factory,self.dropbox_client_factory)
		self.httpd.serve_forever()

	

	