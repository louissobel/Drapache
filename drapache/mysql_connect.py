"""
Low level API for finding our mysql database, and returning a connection to it
I am not trying to wrap MySQLdb here, just the guts of getting a connection object
well i ended up wrapping it a little.
enjoy.

"""


import MySQLdb
from MySQLdb.cursors import Cursor,DictCursor



class MysqlError(Exception):
	
	def __init__(self,message,errcode=0):
		Exception.__init__(self,message)
		self.errcode = errcode
	
class DBConnection:
	"""
	An object oriented wrapper around a mysql connection
	create it, and the connection is automatically established
	to access the raw API, just use the .db attribute (it is the raw connection)
	"""
	
	def __init__(self,mysql_dict=None):
		self.db = get_db_connection(mysql_dict)
		
	def execute_query(self,query_string,params=None,result_type='DICT'):
		"""
		Executes the given query, and returns a generator containing the rows
		row type can be either DICT, returning a dictionary per row
			or 'LIST' which will return a list per row
		"""
		
		if result_type == 'DICT':
			cursor = self.db.cursor(DictCursor)
		elif result_type == 'LIST':
			cursor = self.db.cursor(Cursor)
		else:
			raise ValueError("result_type must be DICT or LIST")
		
		try:
			if params is None:
				cursor.execute(query_string)
			else:
				cursor.execute(query_string,params)
		except MySQLdb.Error as e:
			#args is a tuple of (errcode,message)
			raise MysqlError(e.args[1],e.args[0])
			
		
		return query_result_set(cursor)
		
	def execute_many(self,query_string,params,result_type='DICT'):
		
		if result_type == 'DICT':
			cursor = self.db.cursor(DictCursor)
		elif result_type == 'LIST':
			cursor = self.db.cursor(Cursor)
		else:
			raise ValueError("Only options for result type is 'DICT' or 'LIST'")
		
		try:
			cursor.executemany(query_string,params)
		except MySQLdb.Error as e:
			raise MysqlError(e.args[1],e.args[0])
		
		return query_result_set(cursor)
		
	def close(self):
		self.db.close()
		
	def escape_string(self,in_string):
		return self.db.escape_string(in_string)
		
	def get_mysql_list(self,input_sequence):
		return "("+','.join(str(s) for s in input_sequence)+")"


def _get_db_params(param_dict):
	"""
	gets the database connection information
	returns it as a dict
	"""
	if param_dict is None:
		import dropache_dbconfig as config
		
		param_dict = {}
		param_dict['user'] = config.USER
		param_dict['passwd'] = config.PASS
		param_dict['host'] = config.HOST
		param_dict['db'] = config.DB
	
	param_dict['use_unicode'] = True
	
	return param_dict
	
def get_db_connection(param_dict):
	param_dict = _get_db_params(param_dict)
	try:
		return MySQLdb.connect(**param_dict)
	except MySQLdb.MySQLError:
		raise MysqlError("Unable to connect to mysql database")
		
		
def query_result_set(cursor):
	
	#for row in cursor.fetchall():
	#	yield row
	#cursor.close()
	#raise StopIteration
	while True:
		row = cursor.fetchone()
		if row is None:
			cursor.close()
			raise StopIteration
		else:
			yield row