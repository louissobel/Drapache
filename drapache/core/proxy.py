"""
Implements the interaction with the dropbox api
"""

import os.path
import re

import dropbox

from drapache import dbpy, util, settings

from drapache.util.http import Response

#loading some settings
HIDE_UNDERSCORES = getattr(settings, 'HIDE_UNDERSCORES', True)
REPORT_DELETED = getattr(settings, 'REPORT_DELETED', False)

PATH_HANDLERS = getattr(settings,'PATH_HANDLERS',True)


class DropboxProxy:
	"""
	The class responsable for hitting the dropbox and delegating to the correct file
	should this class get the dropbox client as well? that would be make more sense i think
	"""
	
	
	def __init__(self,client):
		self.client = client
		
	def serve(self, request):
		"""
		serves the given request, returning a Response Object

		"""
		
		#anything prefixed with '_' is not accessable if HIDE_UNDERSCORES is set
		if HIDE_UNDERSCORES:
    		path_components = path.split('/')
    		for component in path_components:
    			if component.startswith('_'):
    				return Response(403,'Forbidden',error=True)
		
		
		try:
			#fuck this extra request... is there a way to avoid it?
			#i don't think so.
			#get_file_and_metadata does not work for a directory,
			#so given that i cannot know if path is a directory or not,
			#it seems that I have to first get metadata before and filedownload can occur
			meta_info = self.client.metadata(path)
			
			#### checking for the is_Deleted flag
            if meta_info.get('is_deleted'):
                if REPORT_DELETED:
				    return Response(410,"File is deleted",error=True)
				else:
				    return Response(404,"File not found",error=True)
				
			# ok now send it on to the handlers!
			return self.handle(request, meta)
			

		
		except dropbox.rest.ErrorResponse as e:
		    # maybe this should just be a regular generic 500 for privacy?
		    # unless debug flag is set?
			return Response(e.status,e.reason,headers=e.headers,error=True)
			
		
			
			
	def handle(self, request, meta):
	    
		for path_handler in PATH_HANDLERS
			if path_handler.check(request, meta):
				return path_handler(request, meta, self)
		
		#if we get to here we have to return an error
		#415 is unsupported media type, by the way
		#maybe this should only happen if a debug flag is set and otherwise 500?
		return Response(415,'No Handler installed for given path',error=True)
		
		

