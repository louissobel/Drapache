"""
Module for handling users, the oauth tokens

THIS COULD AND SHOULD BE OPTIMIZE WITH CACHEING!!!!
"""
import mysql_connect

class SubdomainException(Exception):
	pass


class SubdomainManager:
	"""
	Base class for subdomain manager
	really an interface
	"""
		
	def get_token(self,subdomain):
		"""
		Returns a tuple of (oauth_token,oauth_token_secret)
		If it exists, or None if it does not
		Raises a SubdomainException if there is a problem looking up the subdomain
		"""
		raise SubdomainException("get token not implemented")
		
class MysqlSubdomainManager(SubdomainManager):
	
	def __init__(self,mysql_dict):
		self.db_connection = mysql_connect.DBConnection(mysql_dict)	
	
	def get_token(self,subdomain):
		"""
		returns a (oauth_token,oauth_token_secret) tuple for the given user, or None
		"""
		try:
			SUBDOMAIN_QUERY = "SELECT oauth_token,oauth_token_secret FROM subdomains WHERE subdomain=%s"
			result = self.db_connection.execute_query(SUBDOMAIN_QUERY,subdomain)
			result_list = list(result)
			if result_list:
				row = result_list[0]
				return (row['oauth_token'],row['oauth_token_secret'])
			else:
				return None
		except Exception as e:
			raise SubdomainException(e.message)
			
class FlatFileSubdomainManager(SubdomainManager):
	
	def __init__(self,filename):
		"""
		reads the file into memory
		subdomain|oauth_token|oauth_token_secret
		"""	
		self.subdomains_oauth_map = {}
		f = open(filename)
		for line in f:
			line = line.strip()
			subdomain,oauth_token,oauth_token_secret = line.split('|')
			self.subdomains_oauth_map[subdomain] = (oauth_token,oauth_token_secret)
		f.close()
	
	def get_token(self,subdomain):
		return self.subdomains_oauth_map.get(subdomain)
