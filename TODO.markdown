Things that can be done from here:
-----------------


- Make more subdomain managers / improve the Mysql one with cacheing.
- this is important because the subdomain lookup occurs for every request
	- redis
	- local in - process cache? due to forking I don't think would help?
	- memcache?
	
	
- Make a dropbox client pool so that steps towards asynchronous API access can be taken
- Implement asynchronous IO from dbpy files
- Write more frontends (torndo, wsgi?), get the twisted one to work
	- pretty simple to do, as the frontend just needs to create a drapache.dbapi.server.FileServer
      from a dropbox.DropboxClient and a drapache.util.http.Request
