"""
The http server implementation
"""

import BaseHTTPServer
import SocketServer
import re
import os
import sys
import urlparse
import urllib

import subdomain_managers

import threading

import dbapiserver

from twisted.web import server, resource
from twisted.internet import threads, reactor, defer

ErrorPage = resource.ErrorPage

class DrapacheTwistdResource(resource.Resource):

	isLeaf = True
	
	def __init__(self,subdomain_manager_factory,dropbox_client_factory):
		self.get_subdomain_manager = subdomain_manager_factory
		self.get_dropbox_client = dropbox_client_factory
		
	def render_GET(self,request):
		
		try:
			host_string = request.getHeader("Host")
			host_rest = host_string.split(".",1) #at most one split
			if len(host_rest) == 1:
				subdomain = None
			else:
				subdomain = host_rest[0]
				
			path = request.path
			query_dict = request.args
			query_string = urllib.urlencode(request.args)
		
			if subdomain is None:
				return ErrorPage(400,"Dropache requires a username as the route",None).render(request)
			
			
			subdomain_manager = self.get_subdomain_manager()
		
			try:
				subdomain_exists = subdomain_manager.check_subdomain(subdomain)
			except subdomain_managers.SubdomainException as e:
				return ErrorPage(503,"Error in subdomain lookup:\n"+e.message,None).render(request)
		
		
			if not subdomain_exists:
				return ErrorPage(404,"Subdomain %s does not exist"%subdomain,None).render(request)
				return None
			
			
			try:
				subdomain_token = subdomain_manager.get_token(subdomain)
			except subdomain_managers.SubdomainException as e:
				return ErrorPage(503,"Error in subdomain lookup:\n"+e.message,None).render(request)
			
			subdomain_client = self.get_dropbox_client(subdomain_token)
		
			file_server = dbapiserver.FileServer(subdomain_client,query_dict,query_string)
			
			
			#i think i have to overload this beause of threads?
			#deferred = threads.deferToThread(file_server.serve,path)
			deferred = defer.Deferred()
			def on_finish(success,result):
				sys.stderr.write("at leat the thread finished\n")
				if success:
					sys.stderr.write("success\n")
					reactor.wakeUp()
					
					reactor.callFromThread(deferred.callback,result)
				else:
					sys.stderr.write("fail\n")
					reactor.callFromThread(deferred.errback,result)
					
			reactor.getThreadPool().callInThreadWithCallback(on_finish,file_server.serve,path)
			
			
			
			def response_failed(err,deferr):
				sys.stderr.write('foo')
				deferr.cancel()
					
			def response_errback(err):
				sys.stderr.write('here;!!!\n')
			
			def response_callback(response):
				sys.stderr.write('hmm\n')
				if response.error:
					#ErrorPage(response.status,response.body,None).render(request)
					request.write("fuck")
					request.finish()
		
				else:
					request.setResponseCode(response.status)
					for h,v in response.headers.items():
						request.setHeader(h,v)
					request.write(str(response.body))
					request.finish()
					
			request.notifyFinish().addErrback(response_failed,deferred)
			deferred.addErrback(response_errback)
			deferred.addCallback(response_callback)
			
			return server.NOT_DONE_YET

		
		except Exception as e:
			sys.stderr.write('hmmm!!!ahaha\n')
			return ErrorPage(500,str(e),None).render(request)

	

