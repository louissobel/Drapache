"""
HTTP utility classes
Containers for request and response data
"""

class ResponseObject:
	
	def __init__(self,status,body,headers=None,error=False):
		self.status = status
		self.body = body
		self.error = error
		if headers is None:
			self.headers = {}
		else:
			self.headers = headers
			
	def set_header(self,key,value):
		self.headers[key] = value
		
class RequestObject:
	
	def __init__(self):
		self.headers = {}
		self.query_string = None
		self.query_params = None