from httpserver import DropboxMultiThreadHTTPServer,DropboxHTTPRequestHandler

class Drapache:
	
	
	def __init__(self):
		self.port = None
		self.subdomain_manager_factory = None
		self.dropbox_client_factory = None
		
	def start(self):
		
		assert self.port
		assert self.subdomain_manager_factory
		assert self.dropbox_client_factory
		
		
		server_address = ('0.0.0.0',self.port)
		self.httpd = DropboxMultiThreadHTTPServer(server_address,DropboxHTTPRequestHandler)
		self.httpd.set_config(self.subdomain_manager_factory,self.dropbox_client_factory)
		self.httpd.serve_forever()
		
	