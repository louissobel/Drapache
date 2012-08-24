import drapache
import os
import sys
import config
		
def run():

	instance = drapache.Drapache()
	instance.port = int(os.environ.get('PORT',config.DEFAULT_PORT))
	instance.subdomain_manager_factory = subdomain_manager_factory
	instance.dropbox_client_factory = dropbox_client_factory
	
	sys.stderr.write("Starting drapache instance on port %d\n"%instance.port)
	instance.start()

if __name__=="__main__":
	
	run()