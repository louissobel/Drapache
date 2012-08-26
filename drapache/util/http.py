"""
HTTP utility classes
Containers for request and response data
"""

class Response:
    
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
        
class Request:
    
    
    def __init__(self,
                host,
                headers,
                method,
                path,
                get_params=None,
                query_string='',
                post_params=None,
                ):
        self.host = host
        self.headers = HeaderDict(headers)
        self.method = method
        self.path = path
        self.folder = path.rsplit('/',1)[0] + '/'
        self.get_params = get_params
        self.query_string = query_string
        self.post_params = post_params
        
        
class HeaderDict:
    
    def __init__(self, headers=None):
        self._inner = {}
        if headers:
            for k, v in headers.items():
                self._inner[k.upper()] = v
                
    def get(self, header, default=None):
        return self._inner.get(header.upper(), default)
    
    
    