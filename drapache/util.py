"""
Refactoring utilitys
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
		
			
			
			
class DropacheException(Exception):
	
	def __init__(self,status,message=""):
		
		self.status = status
		self.message = message
		
