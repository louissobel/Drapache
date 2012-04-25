import sys

import config
import dropbox

APP_KEY = config.APP_KEY
APP_SECRET = config.APP_SECRET


def get_oauth_credentials():
	sess = dropbox.session.DropboxSession(APP_KEY,APP_SECRET,'app_folder')
	rt = sess.obtain_request_token()
	url = sess.build_authorize_url(rt)
	sys.stderr.write("Go to the following url, then press enter when you have authorized your app:\n%s\n"%url)
	raw_input()
	at = sess.obtain_access_token(rt)
	return at
	
def generate_flat_file_line(subdomain):
	oauth_token = get_oauth_credentials()
	return "%s|%s|%s" % (subdomain,oauth_token.key,oauth_token.secret)
	
if __name__ == "__main__":
	
	try:
		subdomain = sys.argv[1]
	except IndexError:
		sys.stderr.write("You must specify a subdomain that you are registering\n")
		sys.exit(1)
	
	print generate_flat_file_line(subdomain)
	
	
	