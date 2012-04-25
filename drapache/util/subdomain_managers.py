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
	
	def check_subdomain(self,subdomain):
		raise SubdomainException("check subdomain not implemented")
		
	def get_token(self,subdomain):
		raise SubdomainException("get token not implemented")
		
class MysqlSubdomainManager(SubdomainManager):
	
	def __init__(self,mysql_dict):
		self.db_connection = mysql_connect.DBConnection(mysql_dict)
			
	
	def check_subdomain(self,subdomain):
		"""
		Returns a boolean whether or not this is a valid user
		"""
		try:
			CHECK_SUBDOMAIN = "SELECT count(*) as count FROM subdomains WHERE subdomain=%s"
			result = self.db_connection.execute_query(CHECK_SUBDOMAIN,subdomain)
			return result.next()['count'] == 1
		except Exception as e:
			raise SubdomainException(e.message)
	
	
	def get_token(self,subdomain):
		"""
		returns a (oauth_token,oauth_token_secret) tuple for the given user, or None
		"""
		try:
			SUBDOMAIN_QUERY = "SELECT oauth_token,oauth_token_secret FROM subdomains WHERE subdomain=%s"
			result = self.db_connection.execute_query(SUBDOMAIN_QUERY,subdomain)
			row = result.next()
			return (row['oauth_token'],row['oauth_token_secret'])
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

	def check_subdomain(self,subdomain):
		return subdomain in self.subdomains_oauth_map
	
	def get_token(self,subdomain):
		return self.subdomains_oauth_map.get(subdomain)
			



