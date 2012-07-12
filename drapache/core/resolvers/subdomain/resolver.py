from drapache import settings
from drapache.util.http import Response
from drapache.dbapi import access  

import dropbox  

import backends

from backends import SubdomainException


class SubdomainResolver:
    """
    This class resolves based on the first part of the host field
    It can have different subdomain storage classes defined, a setting
    """
    
    def resolve(self, request):
        
        #ok first i have to parse out the first subdomain from the host attribute
        # of the incoming request
        
        #pulling out the host
		host_string = request.host
		host_rest = host_string.split(".",1) #at most one split
		if len(host_rest) == 1:
			return Response(400, "Subdomain Resolver requires that there be a subdomain! Host: %s" request.host, error=True)
		else:
			subdomain = host_rest[0]
		
        
        
        
        #i need to get an instance of the storage class
        SUBDOMAIN_BACKEND = getattr(settings,'SUBDOMAIN_RESOLVER_BACKEND',backends.FlatFileSubdomainBackend)
        
        try:
            backend_instance = SUBDOMAIN_BACKEND()
            oauth_token_pair = backend_instance.get_token(request)
            
            if oauth_token_pair is None:
				return Response(404,"Subdomain %s does not exist"%subdomain, error=True)
            
        except SubdomainException as e:
            return Response(503, "Error in subdomain lookup using SubdomainResolver:\n%s"%e.message, error=True)

        
        OAUTH_TOKEN, OAUTH_TOKEN_SECRET = oauth_token_pair
        
        
        try:
            DROPBOX_APP_KEY = settings.DROPBOX_APP_KEY
            DROPBOX_APP_SECRET = settings.DROPBOX_APP_SECRET
        except AttributeError:
            return Response(500, "DROPBOX_APP_KEY nad DROPBOX_APP_SECRET must be defined")
            
        
        try:
            client_creator = access.DropboxClientCreator(DROPBOX_APP_KEY, DROPBOX_APP_SECRET)

            return client_creator.get_client(OAUTH_TOKEN, OAUTH_TOKEN_SECRET)

        except dropbox.rest.ErrorResponse as e:
            return Response(e.status,e.reason,headers=e.headers,error=True)
            
        
