Things that can be done from here:
======================

- TESTS.
	- enough said. first priority; it has become way too big to test comprehensively by hand.

- Make more subdomain managers / improve the Mysql one with cacheing.
- this is important because the subdomain lookup occurs for every request
	- redis
	- local in - process cache? due to forking I don't think would help?
	- memcache?
	
	
- Make a dropbox client pool so that steps towards asynchronous API access can be taken

- Implement asynchronous IO from dbpy files
	- this is important... very slow when there are multiple files being acted on by a .dbpy script
	- deferred/callback model is what I am thinking right now

- Write more frontends (torndo, wsgi?), get the twisted one to work
	- pretty simple to do, as the frontend just needs to create a drapache.dbserver.DropboxServer
      from a dropbox.client.DropboxClient and a drapache.util.http.Request, and call serve on it to get a 
	  drapache.util.http.Response

- Also, I think there is room for a lot of cacheing... maybe of dropbox clients?

- Some kind of global configuration mechanism for the server itself... like debug, how to handle index files, dbpy timeout, etc

- I haven't really thought about how much memory could be used, because all files as well as the output of .dbpy scripts
  is saved in memory. Limit this somehow/use tempory files?

- Writing blog.drapache was a pain because, for example, when I made a small change is CSS I had to wait a while before 
  seeing what it looked like in the browser (because of the slow page load times + the dropbox sync delay).
  
  A solution to this would be to create a mock DropboxClient object that can be substituted for the real one while debugging.
  This mock object would run on the _local_ filesystem, but if the server is started in the root of the App folder that the server
  has access to, it would act exactly like it was the actual DropboxFolder. This would really speed up development time for larger
  sites (until asynchronous dropbox IO gets implemented, and even after that)

