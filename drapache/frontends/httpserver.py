"""
The http server implementation
"""

import BaseHTTPServer
import SocketServer
import re
import os
import sys
import urlparse
import traceback

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
			request.subdomain = subdomain
			request.headers = self.headers
		
			#pulling out the request path and query from the url
			path,query_string = self.parse_raw_path(self.path)
		
			#parsing the query
			if query_string is not None:
				get_params = urlparse.parse_qs(query_string)
			else:
				get_params = None
		
			#setting more request variables
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
		
		except Exception as e:
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
		
		
class DropboxForkingHTTPServer(SocketServer.ForkingMixIn,BaseHTTPServer.HTTPServer):
	
	def set_config(self,subdomain_manager_factory,dropbox_client_factory):
		self.get_subdomain_manager = subdomain_manager_factory
		self.get_dropbox_client = dropbox_client_factory
		
	
	#catchall errors
	def finish_request(self,*args,**kwargs):
		try:
			BaseHTTPServer.HTTPServer.finish_request(self,*args,**kwargs)
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

	

	