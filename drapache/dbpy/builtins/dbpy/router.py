"""
This is a router for dbpy to make it act like Flask i guess

first attempt
"""




class Router:


	def __init__(dbpy):
		self.dbpy = dbpy
		self.route_hash = {}

	def route(self,location):

		def decorator(function):

			self.route_hash[location] = function
			return function

		return decorator

	def __call__(self):

		dbpy = self.dbpy
		request_route = self.dbpy.http.request.query_string
		if request_route is None:
			#do a redirect
			redirect_location = "%s?/" % (dbpy.http.request.path)
			dbpy.redirect(redirect_location)
			
		
		#redirect stuff.
		if not request_route.endswith('/'):
			#check if it is there with a slash
			route_with_slash = request_route + '/'
			if route_with_slash in self.route_hash:
				#then i have to redirect
				redirect_location = "%s?%s" % (dbpy.http.request.path,route_with_slash)
				self.dbpy.redirect(redirect_location)
				
		view_function = self.route_hash.get(request_route)
		
		if view_function is None:
			#ok, so its not there. wah.
			#so lets try to render a static file at that location
			#later
			#for now, just throw a 404
			self.dbpy.http.error(404,'No function for that route')
		
		
		#look up the route.
		#if there is nothing there, look for a static file
		#but if there is something there, serve
		#serve an error if we have to
