"""
Implements the interaction with the dropbox api
"""

import os.path
import re

import dropbox

from drapache import dbpy
from drapache import util
from drapache.util.http import Response

import dbfilehandlers


class DropboxServer:
	"""
	The class responsable for hitting the dropbox and processing the results
	
	most of the power of the service will come from here
	"""
	
	
	def __init__(self,client,request):
		self.client = client
		self.request = request
		self.handlers = dbfilehandlers.get_handlers()
		
	def serve(self):
		"""
		serves the given path, returning a Response Object
		
		some special rules
		- if it is a directory,
			returns an indexed list of the files
		- if it is a directory without a trailing slash,
			returns a redirect request (these will also be able to come fro)
		"""
		
		request = self.request
		client = self.client
		path = request.path
		
		#anything prefixed with '_' is not accessable
		path_components = path.split('/')
		for component in path_components:
			if component.startswith('_'):
				return Response(403,'Forbidden',error=True)
		
		
		try:
			#fuck this extra request... is there a way to avoid it? probably
			meta_info = self.client.metadata(path)
			
			#### checking for the is_Deleted flag
			try:
				if meta_info['is_deleted']:
					return Response(410,"File is deleted",error=True)
			except KeyError:
				pass #its not deleted
				
			#ok. here is were i need to call the file thing
			return self._serve_file(meta_info,path)

				
		except dropbox.rest.ErrorResponse as e:
			return Response(e.status,e.reason,headers=e.headers,error=True)
			
			
	def _serve_file(self,meta_info,path):
		for handler in self.handlers:
			checkfunc = handler['check']
			if checkfunc(meta_info):
				return handler['handler'](meta_info,path,self)
		#if we get to here we have to return an error
		#415 is unsupported media type, by the way
		return Response(415,'No Handler installed for given path',error=True)
		
		

		
		
	def _get_content_type(self,file_meta):
		given = file_meta['mime_type']
		if given.startswith('text/x-'):
			return 'text/plain'
		else:
			return given
		
		

