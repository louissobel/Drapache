import drapache
import import_utils

def get_response(request):
    #getting a dropbox client using the resolver
    dropbox_resolver_string = getattr(drapache.settings, 'DROPBOX_RESOLVER', 'drapache.core.resolvers.SimpleResolver')
    dropbox_resolver = import_utils.import_module_from(dropbox_resolver_string)
    dropbox_client = dropbox_resolver().resolve(request)
    
    # we have to check is dropbox_client is instance of request
    # (which means we have to return it)
    # this happens if the resolver short-circuits
    if isinstance(dropbox_client, drapache.util.http.Response):
        response = dropbox_client
    else:
        response = drapache.core.DropboxProxy(dropbox_client).serve(request)
        
    return response