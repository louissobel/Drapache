"""
refactors out the logic of handling files from the server itself

"""
from drapache import dbpy, settings
import re
import os
from drapache import util
from drapache.util.http import Response

from drapache import dbapi
import jinja2

import markdown

print "ME"

class DropboxPathHandler:
    
    def check(self, request, meta):
        raise NotImplementedError
        
    def __call__(self, request, meta, proxy):
        raise NotImplementedError

        
### static handler
class StaticHandler(DropboxPathHandler):
    
    def check(self, request, file_meta):
        """
        A fallback handler, so returns true
        """
        return True

    def __call__(self, request, file_meta, proxy):
        """
        downloads and serves the file in path
        """
        path = file_meta['path']
        f = proxy.client.get_file(path).read()
        if f.startswith('#DBPYEXECUTE'):
            #allows arbitrary text files to be run as dbpy code. security risk?
            #any way, by returning None we retart the handler search
            request.FORCE_DBPY = True
            return None
        
        headers = {}

        content_type = file_meta['mime_type']
        if content_type.startswith('text/x-'):
            content_type = 'text/plain'
            
        headers['Content-Type'] = content_type

        return Response(200,f,headers)
        

        
    
    
#### directory handler
class DirectoryHandler(DropboxPathHandler):
    
    def check(self, request, meta):
        return meta['is_dir']
    
    def __call__(self, request, meta, proxy):
        """
        called when asked to serce a directory
        check for the presence of an index file and serve it (without redirect of course)
        or present an index if there isn't one
        lets lok through meta_info[contents], anything with index is of interest
        precedence is .dbpy, .html, .txt, and thats it

        for now, just auto generate an index, fun!
        """
    
        #redirect like apache if we don't end the path with '/'
        if not request.path.endswith('/'):
            redirect_location = request.path+'/'
            if request.query_string:
                redirect_location += '?'+ request.query_string
            
            return Response(301,'redirect',headers={'Location':redirect_location})


        #ok, lets build our index thing
        index_file_prefixes = getattr(settings, 'INDEX_PREFIXES',('index',))
        extensions_precedence = getattr(settings,'INDEX_EXTENSIONS',('dbpy','html','txt',))

        #build the re
        re_string = "^(%s)\.(%s)$" % ( '|'.join(index_file_prefixes), '|'.join(extensions_precedence) )
        index_re = re.compile(re_string)

        index_paths = {}

        for file_meta in meta['contents']:
            file_path = file_meta['path']
            base_name = os.path.basename(file_path)

            if index_re.match(base_name):
                index_paths[base_name] = file_meta


        for prefix in index_file_prefixes:
            for extension in extensions_precedence:
                base_name = "%s.%s" % (prefix,extension)
                if base_name in index_paths:
                    new_file_meta = index_paths[base_name]
                    request.path = request.path + base_name
                    return proxy.handle(request, new_file_meta)

        #there are no index files, so lets return a default one
        index_file = util.index_generator.get_index_file(meta['contents'], request.path, proxy.client) #TODO fix this
        
        return Response(200, index_file)
    
    
########## dbpy handler
class DBPYHandler(DropboxPathHandler):
    def check(self, request, meta):
        path = meta['path']
        
        if hasattr(request, 'NO_DBPY'):
            return False
        else:
            if hasattr(request, 'FORCE_DBPY'):
                return True
            else:
                return path.endswith('.dbpy')

    def __call__(self, request, meta, proxy):

        path = meta['path']
        f = proxy.client.get_file(path).read()
        
        if f.startswith("#NOEXECUTE"):
            # short circuit
            request.NO_DBPY = True
            return None
        
        
        
        
        
        return dbpy.execute(f, request, proxy)
    
            
        
####markdown handler
class MarkdownHandler(DropboxPathHandler):
    
    def check(self, request, meta):
        path = meta['path']
        
        markdown_extensions = getattr(settings,'MARKDOWN_EXTENSIONS',('md','mkd','mkdn','mdown','markdown'))
        markdown_extension_re = re.compile("\.(%s)$" % '|'.join(markdown_extensions))
        
        return bool( markdown_extension_re.search( os.path.basename(path) ) )

    def __call__(self, request, meta, proxy):
        
        markdown_template_path = getattr(settings,'MARKDOWN_TEMPLATE_PATH',None)
        
        if markdown_template_path:
            env = jinja2.Environment(loader=dbapi.jinja.DropboxLoader(proxy.client,''))
            
            try:
                template = env.get_template(markdown_template_path)
            except dbapi.jinja.TemplateNotFound:
                return Response(404,"unable to find markdown template at %s"%markdown_template_path, error=True)
            
        else:

            template = jinja2.Template("""
            <html>
            <head>
                <title>
                    {{ base_path }} | Markdown
                </title>
            </head>
    
            <body>
                {{ body }}
            </body>
            </html>
            """)
        
        base_path = file_meta['path']
        body = markdown.markdown(proxy.client.get_file(path).read())
        
        page = template.render(body=body,base_path=base_path)
        headers = {'Content-Type':'text/html'}
        return Response(200,page,headers)
    
    
