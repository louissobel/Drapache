"""
Defines utility classes for connecting to dropbox
"""

import dropbox


#credentials for Dropaches



class DropboxClientCreator:
	
	
	def __init__(self,app_key,app_secret,access_type='app_folder'):
		
		self.app_key = app_key
		self.app_secret = app_secret
		self.access_type = access_type
		
		
	def get_client(self,oauth_token,oauth_token_secret):
		
		sess = dropbox.session.DropboxSession(self.app_key,self.app_secret,self.access_type)
		sess.set_token(oauth_token,oauth_token_secret)
		client = dropbox.client.DropboxClient(sess)
		return client
		
		
