"""
refactors out the logic of handling files from the server itself

"""
from drapache import dbpy
import re
import os
from drapache import util
from drapache.util.http import Response

import markdown

def register(handler_list,checkfunction,func):
	
		
	handler_list.append({'check':checkfunction,'handler':func})


def get_handlers():
	

	handler_list = []
	
	#lookup order:
	
	#directory
	#dbpy
	#markdown
	#static
	
	#directory
	register(handler_list,check_directory,serve_directory)
	#dbpy
	register(handler_list,check_dbpy,serve_dbpy)
	#markdown
	register(handler_list,check_markdown,serve_markdown)
	#the rest
	register(handler_list,check_static,serve_static)
	
	return handler_list
		
### static handler
def check_static(file_meta):
	return True

def serve_static(file_meta,request_path,server):
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
	
	
#### directory handler
def check_directory(directory_meta):
	return directory_meta['is_dir']
	
def serve_directory(directory_meta,request_path,server):
	"""
	called when asked to serce a directory
	check for the presence of an index file and serve it (without redirect of course)
	or present an index if there isn't one
	lets lok through meta_info[contents], anything with index is of interest
	precedence is .dbpy, .html, .txt, and thats it

	for now, just auto generate an index, fun!
	"""
	
	#redirect like apache if we don't end the path with '/'
	if not request_path.endswith('/'):
		redirect_location = request_path+'/'
		if server.request.query_string:
			redirect_location += '?'+server.request.query_string
			
		return Response(301,'redirect',headers={'Location':redirect_location})


	#ok, lets build our index thing

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
			new_file_meta = index_paths[extension]
			new_request_path = request_path + os.path.basename(new_file_meta['path']) #we know request path ends with a '/'
			return server._serve_file(new_file_meta,new_request_path)

	#there are no index files, so lets return a default one
	index_file = util.index_generator.get_index_file(directory_meta['contents'],request_path,server.client)
	return Response(200,index_file)
	
	
########## dbpy handler
def check_dbpy(file_meta):
	path = file_meta['path']
	return path.endswith('.dbpy')

def serve_dbpy(file_meta,request_path,server):
	path = file_meta['path']
	f = server.client.get_file(path).read()
	if f.startswith("#NOEXECUTE"):
		#allows these files to be shared without getting executed
		headers = {'Content-type':'text/plain'}
		return Response(200,f,headers)

	param_dict = dict(client=server.client,request=server.request)
	return dbpy.execute.execute(f,**param_dict)
	
			
		
####markdown handler
def check_markdown(file_meta):
	path = file_meta['path']
	markdown_extension_re = re.compile("\.(md|mkd|mkdn|mdown|markdown)$")
	return bool( markdown_extension_re.search( os.path.basename(path) ) )

def serve_markdown(file_meta,request_path,server):

	page_template = """
	<html>
	<head>
		<title>
			%s
		</title>
	</head>
	
	<body>
		%s
	</body>
	</html>
	"""
	path = file_meta['path']
	page_title = "%s | Markdown" % path
	page_body = markdown.markdown(server.client.get_file(path).read())
	
	page = page_template % (page_title,page_body)
	
	headers = {'Content-Type':'text/html'}
	return Response(200,page,headers)
	
	
