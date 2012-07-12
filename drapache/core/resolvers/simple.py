from drapache import settings
from drapache.util.http import Response
from drapache.dbapi import access  

import dropbox  
    
class SimpleResolver:
    """
    This class just uses Oauth token and token secret hardcoded into settings.py
    """
    
    
    def resolve(self,request):
        
        for needed in ('OAUTH_TOKEN', 'OAUTH_TOKEN_SECRET', 'DROPBOX_APP_KEY', 'DROPBOX_APP_SECRET'):
            try:
                exec "%s = settings.%s" % (needed, needed)
            except AttributeError:
                return Response(500, "%s must be in settings when using SimpleResolver" % needed,error=True)
                
        
        try:
            client_creator = access.DropboxClientCreator(DROPBOX_APP_KEY, DROPBOX_APP_SECRET)
        
            return client_creator.get_client(OAUTH_TOKEN, OAUTH_TOKEN_SECRET)
        
        except dropbox.rest.ErrorResponse as e:
            return Response(e.status,e.reason,headers=e.headers,error=True)