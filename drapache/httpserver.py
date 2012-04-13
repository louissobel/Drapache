"""
The http server implementation
"""

import BaseHTTPServer
import SocketServer
import re
import os
import sys
import urlparse

import dbapiserver

import subdomain_managers



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
		
		
		try:
			host_string = self.headers.get("Host")
			host_rest = host_string.split(".",1) #at most one split
			if len(host_rest) == 1:
				subdomain = None
			else:
				subdomain = host_rest[0]
		
		
			path,query_string = self.parse_raw_path(self.path)
		
			if query_string is not None:
				query_dict = urlparse.parse_qs(query_string)
			else:
				query_dict = None
		
			if subdomain is None:
				self.send_error(400,"Dropache requires a username as the route")
				return None
			
			
			subdomain_manager = self.server.get_subdomain_manager()
		
			try:
				subdomain_exists = subdomain_manager.check_subdomain(subdomain)
			except subdomain_managers.SubdomainException as e:
				self.send_error(503,"Error in subdomain lookup:\n"+e.message)
				return None
		
		
			if not subdomain_exists:
				self.send_error(404,"Subdomain %s does not exist"%subdomain)
				return None
			
			
			try:
				subdomain_token = subdomain_manager.get_token(subdomain)
			except subdomain_managers.SubdomainException as e:
				self.end_error(503,"Error in subdomain lookup:\n"+e.message)
				return None
			
			subdomain_client = self.server.get_dropbox_client(subdomain_token)
		
			file_server = dbapiserver.FileServer(subdomain_client,query_dict,query_string)
		
			response = file_server.serve(path)
			
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
			self.send_error(500,str(e))
		
		
	def parse_raw_path(self,path):
		"""
		pulls out the user, the path, and the query if any
		
		the routing for now is going to be that the user is the first "directory"
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
		
		
class DropboxMultiThreadHTTPServer(SocketServer.ForkingMixIn,BaseHTTPServer.HTTPServer):
	
	def set_config(self,subdomain_manager_factory,dropbox_client_factory):
		self.get_subdomain_manager = subdomain_manager_factory
		self.get_dropbox_client = dropbox_client_factory
		
	
	#catchall errors
	def finish_request(self,*args,**kwargs):
		try:
			BaseHTTPServer.HTTPServer.finish_request(self,*args,**kwargs)
		except Exception as e:
			sys.stderr.write("Uncought response exception: %s\n"%str(e))

	

	