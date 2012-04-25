Drapache
=================
_apache for your dropbox_

About
----------
A python server that uses the dropbox API to serve files that are hosted on dropbox. It will not be particularly useful
to a developer who is comfortable with git, heroku, ftp, or another method of hosting a website. It will be useful, however,
to people who are not proficient with these tools. It is extremely simple because whatever is in the Drapache folder in the users
dropbox /Apps folder will be immediately available on the internet.
Get it set up at [get.drapache.com](http://get.drapache.com)

.dbpy
-----------
Besides being able to serve static files, Drapache also implements a rudimentary CGI/PHP-like framework in python.
Files that have the extension .dbpy or start with the string "#DBPYEXECUTE" will be treated as "dropbox python" files
and executed by the Drapache server, returning anything that is printed to standard out to the clients browser.

Although far from finished, the dbpy framework is enough for beginning programmers to get started building dynamic websites.

Misc. Features
----------------
It will create an index for a folder if one doesn't exist, using a template found in Drapache/_templates/
Files are folders that begin with '_' will not be served, returning instead a 403 Forbidded HTTP response.

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
*	add more testing subdomains by repeating step 3 for other subdomains
*	There are other ways of managing subdomains than a flat file.. look in subdomain_manager.py for the base class
	and an implementation of managing subdomains with mysql
*	This will create a folder in your dropbox /Apps folder with the name whatever app you created in step 2, and
	your local instance will serve from that folder, _not_ the Drapache folder that you will get if you sign up through get.drapache
