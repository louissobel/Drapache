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
			
			
			
class DropacheException(Exception):
	
	def __init__(self,status,message=""):
		
		self.status = status
		self.message = message
		
