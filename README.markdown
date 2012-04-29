Drapache
=================
_apache for your dropbox_

About
----------
A python server that uses the dropbox API to serve files that are hosted on dropbox. It will not be particularly useful
to a developer who is comfortable with git, heroku, ftp, or another method of hosting a website. It will be useful, however,
to people who don't know how to use these tools. It's very simple - whatever is in the Drapache folder in the users
dropbox /Apps folder will be immediately available on the internet.
Get it set up at [get.drapache.com](http://get.drapache.com)

.dbpy
-----------
Besides being able to serve static files, Drapache also implements a rudimentary CGI/PHP-like framework in python.
Files that have the extension .dbpy or start with the string "#DBPYEXECUTE" will be treated as "dropbox python" files
and executed by the Drapache server, returning anything that is printed to standard out to the clients browser.

Although far from finished, the dbpy framework is enough for beginning programmers to get started building dynamic websites.
Check out [blog.drapache](http://github.com/louissobel/blog.drapache) (on github too) for a blogging system I scraped together that
runs on drapache and demonstrates what can be done with dbpy.

Misc. Features
----------------
It will create an index for a folder if one doesn't exist, using a template found in Drapache/\_templates/.
Files or folders that begin with '\_' will not be served, returning instead a 403-Forbidden HTTP response.
Right now they _do_ show up in an auto-generated index, but that is for debugging purposes and could be easily changed

Technical
---------------
Working on documenting both the server as well as the dbpy framework.

This is the high level life-cycle of a request:

1. A frontend handles the http request, and creates a Request object. It handles parsing the Host header for the 
   requested subdomain, parsing GET/POST parameters, looking up any dropbox oauth for the requested subdomain,
   and creating a dropbox API client. The frontend passes the request and client off to a DropboxServer.
2. The DropboxServer parses the path, and looks up the metainfo for the file requested. If it is a directory, it goes
   through some logic to create and index page. If it is a file, it downloads it. If it is a static file, it passes it back
   to the frontend, which writes it to the internet. If it is a dbpy file, it passes it, along the request and client, to
   dbpy.execute.
3. dbpy.execute creates a sandbox using the [pysandbox](http://github.com/haypo/pysandbox) module by [haypo](http://github.com/haypo).
   It creates a number of objects necessary to execute a dbpy file, gets a dictionary of the dbpy built-in functions, and creates
   a new thread in which to run the downloaded dbpy script. It creates a new, in memory, stdout, and starts the created thread.
4. This thread activates the sandbox, and calls exec on the downloaded script, capturing any errors. The running script has access
   to the request, response, sessions, templates, and the dropbox file system through the dbpy framework. This thread will be killed by the caller
   after a certain amount of time (right now 25 seconds) and an exception will be raised. Errors in this thread are caught and passed
   back to the caller.
5. Once the thread either finishes or is killed, any clean-up from the dbpy script takes place,
   the fake stdout is replaced with the real stdout, and the error output or actual output of the
   dbpy script is passed back to the DropboxServer with any headers and status code of the new Response.
6. The DropboxServer passes this response back to the frontend, which writes it to the internet.


Running an instance locally
---------------------------
1. make sure that all the requirements present in requirements.txt are satisfied
	(pip install -r requirements.txt will do it, as should starting a new virtualenv I think)
2. Go to dropbox.com/developers and create a new app
3. Fill in the file config.py with the app key and secret of that new app
4. run `python get_dropbox_oauth.py [TESTING_SUBDOMAIN] >> [SUBDOMAIN_FILE]`
	(where TESTING_SUBDOMAIN is the subdomain you want to add to your local instance,
	and SUBDOMAIN_FILE is the name of the file in which you want to save subdomains)
5. In config.py, fill in the SUBDOMAIN_FILE variable with the file path from step 3.
6. Add a line like '127.0.0.1	TESTING_SUBDOMAIN.localhost' to your /etc/hosts file
	(this enables local subdomain routing.. if there is a better way let me know!)
7. Run `python server.py` and you should have a drapache instance on localhost (the default port is 5501)
	
Notes:
*	add more testing subdomains by repeating step 4 for other subdomains
*	There are other ways of managing subdomains than a flat file.. look in subdomain_manager.py for the base class
	and an implementation of managing subdomains with mysql
*	This will create a folder in your dropbox /Apps folder with the name of whatever app you created in step 2, and
	your local instance will serve from that folder, _not_ the Drapache folder that you will get if you sign up through get.drapache
