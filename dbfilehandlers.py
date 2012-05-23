"""
refactors out the logic of handling files from the server itself

"""
from drapache import dbpy


def get_handlers(server):
	
	
	
	handler_hash = {}
	handler_list = []
	
	
	def register(name,checkfunction):
		
		def decorator(func):
			
			handler_hash[name] = func
			handler_list.append({'check':checkfunction,'handler':func})
			
			return func
			
		return decorator
		
	
	
	def _serve_static(file_meta):
		"""
		downloads and serves the file in path
		"""
		path = file_meta['path']
		f = server.client.get_file(path).read()
		if f.startswith('#DBPYEXECUTE'):
			#allows arbitrary text files to be run as dbpy code. security risk?
			#any way, it is like a bypass... back to dbpy
			param_dict = dict(client=server.client,request=server.request)
			return dbpy.execute.execute(f,**param_dict)
		headers = {'Content-type':server._get_content_type(file_meta)}
		return Response(200,f,headers)
		
	def _find_and_serve_index(self,directory_meta,path):
		"""
		called when asked to serce a directory
		check for the presence of an index file and serve it (without redirect of course)
		or present an index if there isn't one
		lets lok through meta_info[contents], anything with index is of interest
		precedence is .dbpy, .html, .txt, and thats it

		for now, just auto generate an index, fun!
		"""
		extensions_precedence = ('dbpy','html','txt')

		#build the re
		re_string = "^index\.(%s)$"%( '|'.join(extensions_precedence) )
		index_re = re.compile(re_string)

		index_paths = {}

		for file_meta in directory_meta['contents']:
			file_path = file_meta['path']
			base_name = os.path.basename(file_path)

			index_re_match = index_re.match(base_name)

			if index_re_match:
				match_type = index_re_match.group(1)
				index_paths[match_type] = file_meta


		for extension in extensions_precedence:
			if extension in index_paths:
				return self._serve_file(index_paths[extension])

		#there are no index files, so lets return a default one
		index_file = util.index_generator.get_index_file(directory_meta['contents'],path,self.client)
		return Response(200,index_file)
	
			
		
	
	#### look up the configuration for the right options!
	
	