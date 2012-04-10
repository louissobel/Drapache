import drapache
import os

import sample_config as config
		
def run():
	
	param_dict = {}
	param_dict['user'] = config.USER
	param_dict['passwd'] = config.PASS
	param_dict['host'] = config.HOST
	param_dict['db'] = config.DB
	def subdomain_manager_factory():
		return drapache.subdomain.MysqlSubdomainManager(param_dict)
		
	#to use a flat file
	def subdomain_manager_factort():
		return drapache.subdomain.FlatFileSubdomainManager(config.SUBDOMAIN_FILE)
		
	dropbox_client_generator = drapache.dropbox_access.DropboxClientCreator(config.APP_KEY,config.APP_SECRET)
	def dropbox_client_factory(token_tuple):
		return dropbox_client_generator.get_client(*token_tuple)
	
	instance = drapache.Drapache()
	instance.port = os.environ.get('PORT',5501)
	instance.subdomain_manager_factory = subdomain_manager_factory
	instance.dropbox_client_factory = dropbox_client_factory
	instance.start()

if __name__=="__main__":
	
	run()