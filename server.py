import drapache
import os
import sys
import config
		
def run():

		
	#to use a flat file
	#where lines are in the format
	#SUBDOMAIN|OAUTH_TOKEN|OAUTH_TOKENSECRET
	def subdomain_manager_factory():
		return drapache.util.subdomain_managers.FlatFileSubdomainManager(config.SUBDOMAIN_FILE)
		
	dropbox_client_generator = drapache.dbapi.access.DropboxClientCreator(config.APP_KEY,config.APP_SECRET)
	def dropbox_client_factory(token_tuple):
		return dropbox_client_generator.get_client(*token_tuple)
	
	instance = drapache.Drapache()
	instance.port = int(os.environ.get('PORT',config.DEFAULT_PORT))
	instance.subdomain_manager_factory = subdomain_manager_factory
	instance.dropbox_client_factory = dropbox_client_factory
	
	sys.stderr.write("Starting drapache instance on port %d\n"%instance.port)
	instance.start()

if __name__=="__main__":
	
	run()