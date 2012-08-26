import drapache
from common import get_response

import urlparse

def WsgiDrapache(environ, start_response):
    
    
    
    """
    host
    headers
    method
    path
    get_params
    query_string
    post_params
    """
    
    ### lets parse out the request!
    request_dict = {}
    
    # all the keys prefixed with HTTP_
    request_dict['headers'] = dict((k[5:].replace('_','-'), v) for k, v in environ.items() if k.startswith('HTTP_'))
    request_dict['host'] = environ['HTTP_HOST']
    request_dict['method'] = environ['REQUEST_METHOD'].upper()
    
    script_name = environ.get('SCRIPT_NAME', '')
    path_info = environ.get('PATH_INFO', '/')
    if not path_info or path_info == script_name:
        # Copied from Django WSGI handler
        path_info = '/'
    request_dict['path'] = '%s%s' % (script_name, path_info)
    
    # getting the query_string
    query_string = environ.get('QUERY_STRING', '')
    if query_string == '':
        query_string = None

    #parsing the query
    if query_string is None:
        get_params = None
    else:
        get_params = urlparse.parse_qs(query_string)
    
    request_dict['get_params'] = get_params
    request_dict['query_string'] = query_string
    
    # parsing the post
    #parsing post parameters if it is a post request
    if request_dict['method'] == 'POST':
        try:
            request_length = int(environ.get('CONTENT_LENGTH'))
        except (ValueError, TypeError):
            request_length = 0 
        body = environ['wsgi.input'].read(request_length)
        post_params = urlparse.parse_qs(body)
        request_dict['post_params'] = post_params


    request = drapache.util.http.Request(**request_dict)
    response = get_response(request)
    
    message = "%d %s" % (response.status, STATUS_CODE_TEXT.get(response.status, 'unknown'))

    # response.headers will be either dictionary or list of tuples
    if isinstance(response.headers, dict):
        out_headers = [(k ,v) for k, v in response.headers.items()]
    else:
        out_headers = response.headers

    start_response(message, out_headers)
    return response.body
  
  
  
# See http://www.iana.org/assignments/http-status-codes
STATUS_CODE_TEXT = {
    100: 'CONTINUE',
    101: 'SWITCHING PROTOCOLS',
    102: 'PROCESSING',
    200: 'OK',
    201: 'CREATED',
    202: 'ACCEPTED',
    203: 'NON-AUTHORITATIVE INFORMATION',
    204: 'NO CONTENT',
    205: 'RESET CONTENT',
    206: 'PARTIAL CONTENT',
    207: 'MULTI-STATUS',
    208: 'ALREADY REPORTED',
    226: 'IM USED',
    300: 'MULTIPLE CHOICES',
    301: 'MOVED PERMANENTLY',
    302: 'FOUND',
    303: 'SEE OTHER',
    304: 'NOT MODIFIED',
    305: 'USE PROXY',
    306: 'RESERVED',
    307: 'TEMPORARY REDIRECT',
    400: 'BAD REQUEST',
    401: 'UNAUTHORIZED',
    402: 'PAYMENT REQUIRED',
    403: 'FORBIDDEN',
    404: 'NOT FOUND',
    405: 'METHOD NOT ALLOWED',
    406: 'NOT ACCEPTABLE',
    407: 'PROXY AUTHENTICATION REQUIRED',
    408: 'REQUEST TIMEOUT',
    409: 'CONFLICT',
    410: 'GONE',
    411: 'LENGTH REQUIRED',
    412: 'PRECONDITION FAILED',
    413: 'REQUEST ENTITY TOO LARGE',
    414: 'REQUEST-URI TOO LONG',
    415: 'UNSUPPORTED MEDIA TYPE',
    416: 'REQUESTED RANGE NOT SATISFIABLE',
    417: 'EXPECTATION FAILED',
    422: 'UNPROCESSABLE ENTITY',
    423: 'LOCKED',
    424: 'FAILED DEPENDENCY',
    426: 'UPGRADE REQUIRED',
    500: 'INTERNAL SERVER ERROR',
    501: 'NOT IMPLEMENTED',
    502: 'BAD GATEWAY',
    503: 'SERVICE UNAVAILABLE',
    504: 'GATEWAY TIMEOUT',
    505: 'HTTP VERSION NOT SUPPORTED',
    506: 'VARIANT ALSO NEGOTIATES',
    507: 'INSUFFICIENT STORAGE',
    508: 'LOOP DETECTED',
    510: 'NOT EXTENDED',
}  

