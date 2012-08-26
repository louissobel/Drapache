"""
The http server implementation
"""

import BaseHTTPServer
import SocketServer
import socket #for socket.error
import re
import os
import sys
import urlparse
import traceback
import threading

import import_utils

import drapache

from common import get_response



class DropboxHTTPRequestHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    """
    This class is responsible for creating the request object
    getting/processing content gets farmed out to a dropbox proxy
    pulling out the proper use and host and subdomain etcetera happens elsewhere too
    """
    
    def do_GET(self):
        return self.serve(method='get')
        
    def do_POST(self):
        return self.serve(method='post')
    
    def serve(self, method=None):
        
        
        try:
            #### Processing the Request
            
            #create an empty request dictionary
            request_dict = {}

            #setting some request variables
            request_dict['host'] = self.headers.get('Host')
            request_dict['headers'] = self.headers
            request_dict['method'] = method
        
            parsed_url_path = urlparse.urlparse(self.path)
            path = parsed_url_path.path
            query_string = parsed_url_path.query
            if path == '':
                path = '/'
            if query_string == '':
                query_string = None
        
            #parsing the query
            if query_string is None:
                get_params = None
            else:
                get_params = urlparse.parse_qs(query_string)
        
            #setting more request variables IMPORTANT. fragile though. sorry
            request_dict['path'] = path
            request_dict['get_params'] = get_params
            request_dict['query_string'] = query_string     
        
            #parsing post parameters if it is a post request
            if method == 'post':
                request_length = int(self.headers.get('Content-length',0))
                body = self.rfile.read(request_length)
                post_params = urlparse.parse_qs(body)
                request_dict['post_params'] = post_params
                
            # create a request from the request dictionary
            request = drapache.util.http.Request(**request_dict)
        
            # get the response
            response = get_response(request)
            
            if response.error:
                self.send_error(response.status,response.body)
                return None
        
            else:
                self.send_response(response.status)
                for h,v in response.headers.items():
                    self.send_header(h,v)
                self.end_headers()
                self.wfile.write(response.body)
                return None
                
        ##### Catchall errors
        except socket.error as e:
            #check if it was a broken pipe
            #... assume it was a broken pipe
            #if it was a broken pipe, the client went away. which is fine. and i don't need a traceback for that.
            #nor should i try to send a 500 message, because there is no way it will get through
            pass
            
        
        except Exception as e:
            ### Caught an error, now attempting to send a 500 server error response
            traceback.print_exc()
            self.send_error(500,str(e))
        
        

        

class ThreadJoiningForkingMixIn(SocketServer.ForkingMixIn):

    """
    Mix-in class to handle each request in a new process.
    COPIED FROM STANDARD LIBRARY
    EXCEPT THAT IT WAITS ON ALL BACKGROUND THREADS TO FINISH BEFORE os._exit-ing
    """

    def process_request(self, request, client_address):
        """Fork a new subprocess to process the request."""
        self.collect_children()
        pid = os.fork()
        if pid:
            # Parent process
            if self.active_children is None:
                self.active_children = []
            self.active_children.append(pid)
            self.close_request(request) #close handle in parent process
            return
        else:
            # Child process.
            # This must never return, hence os._exit()!
            try:
                self.finish_request(request, client_address)
                self.shutdown_request(request)
                
                JOINsTHREADS_TIMEOUT = 10 #we will try for ten seconds to wait for background threads to finish
                JOINTHREADS_INCREMENT = .1 #how long we try to join each thread
                
                been_waiting = 0
                while threading.active_count() > 1 and been_waiting < JOINTHREADS_TIMEOUT: #while there are more threads than this one
                    for thread in threading.enumerate():
                        if not thread is threading.current_thread():
                            thread.join(JOINTHREADS_INCREMENT)
                            been_waiting += JOINTHREADS_INCREMENT               
                
                #at this point, either all background threads have finished or we've been waiting damn long enough
                os._exit(0)
            except:
                try:
                    self.handle_error(request, client_address)
                    self.shutdown_request(request)
                finally:
                    os._exit(1)
        
class DropboxForkingHTTPServer(ThreadJoiningForkingMixIn, BaseHTTPServer.HTTPServer):
        
    
    #catchall errors
    def finish_request(self,*args,**kwargs):
        try:
            BaseHTTPServer.HTTPServer.finish_request(self,*args,**kwargs)
        except socket.error as e:
            sys.stderr.write("[error] %s\n"%"Client went away")
        except Exception as e:
            traceback.print_exc()
            sys.stderr.write("[error] Uncought response exception: %s\n"%str(e))
            
            
class HttpDrapache:

    def start(self,port=8080):
        print "Starting HTTP drapache on port %d" % port
        server_address = ('0.0.0.0',port)
        self.httpd = DropboxForkingHTTPServer(server_address,DropboxHTTPRequestHandler)
        self.httpd.serve_forever()


    

    