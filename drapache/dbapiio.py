"""
Implements a class for locking and unlocking
"""
import uuid
import sys
import StringIO
import re
import dropbox
import json
import time
import os.path
import StringIO
import threading

class ReadableDropboxFile(StringIO.StringIO):
	
	def __init__(self,path,client):
		
		try:
			response = client.get_file(path)
		except dropbox.rest.ErrorResponse:
			#or should i throw an exception? hmmm
			#or should i return none
			raise IOError("Unable to read file")
	
		filestring = response.read()
		response.close()
		
		StringIO.StringIO.__init__(self,filestring)

	def write_error(self,*args,**kwargs):
		raise IOError("Cannot write to a file opened for reading!")
	
	write = write_error
	writelines = write_error


class LiveDropboxFile(StringIO.StringIO):
	
	def __init__(self,path,client,download=True):
		
		self.__open = True
		
		self.path = path
		
		if download:
			readable = ReadableDropboxFile(path,client)
			StringIO.StringIO.__init__(self,readable.read())
			
		else:
			StringIO.StringIO.__init__(self)
		
	def _update(self,client):

		if self.__open:
			self.seek(0)
			client.put_file(self.path,self,overwrite=True)

	def close(self,locker=None):

		if self.__open:

			if locker is not None:
				try:
					self._update(locker.client)
				finally:
					locker.release(self.path)
					self.__open = False
		else:
			pass
			#this allows for mutliple accidental callings .close()


class WritableDropboxFile(LiveDropboxFile):
	
	def __init__(self,path,client,download=True,mode='append'):
		#mode is either write or append
		#if append, we have to download if download is true
		#so we only have to download the file if download is true and the mode is append
		
		do_download = (download and mode == 'append')
		LiveDropboxFile.__init__(self,path,client,do_download,mode)
		if mode == 'append':
			self.seek(0,2)
			
		self.mode = mode
			
	def _update(self,client):
		LiveDropboxFile._update(self,client)
		if self.mode == 'append':
			self.seek(0,2)
		else:
			self.seek(0)
			
			
	def write(self,what):
		
		if not self.__open:
			raise IOError('Cannot write to a closed file')
			
		if self.mode == 'append':
			self.seek(0,2)
		StringIO.StringIO.write(self,what)
		
	def writeline(self,line):
		self.write(line+'\n')
		
	def writelines(self,sequence):
		
		if not self.__open:
			raise IOError('Cannot write to a closed file!')
		
		if self.mode == 'append':
			self.seek(0,2)
		StringIO.StringIO.writelines(self,sequence)
			


			
class JSONDropboxFile(LiveDropboxFile):
	
	def __init__(self,path,client,download=False):
		LiveDropboxFile.__init__(self,path,client,download=download)
		
		#throws a value error if the json isn't good
		if download:
			self.json_object = json.load(self)
		else:
			#caller is responseable for making this into an actual object if it wants
			self.json_object = None
			
		
	def _update(self,client):
		self.seek(0)
		sys.stderr.write(':'+str(self.json_object)+"\n")
		
		try:
			json.dump(self.json_object,self)
			self.truncate()
		except TypeError:
			self.seek(0)
			self.truncate()
			raise TypeError("cannot make a JSON object")
		
		LiveDropboxFile._update(self,client)
		
		
		
		
			
			
			


class DropboxFileLocker:
	
	def __init__(self,client):
		
		self.client = client
		self.open_files = []
		
		
	def lock(self,path,timeout=None):
		#create a client unique key
		#put a file _lockrequest_<client_key>_<filename>
		client = self.client

		request_folder,filename = path.rsplit('/',1)

		client_uuid = uuid.uuid4().hex[:12] #using first 12 digits of uuid
		flag_file = "_lockrequest_%s_%s" % (client_uuid,filename)
		flag_file_path = request_folder + '/' + flag_file


		try:
			client.put_file(flag_file_path,StringIO.StringIO('flag for file %s'%filename))
		except dropbox.rest.ErrorResponse:
			raise IOError('unable to put flag for locking')

		have_write_permission = False
		timedout = False

		lockrequest_regex = re.compile(r"_lockrequest_([0-9a-f]{12})_%s"%re.escape(filename),flags=re.I)
		lock_regex = re.compile(r"_lock_%s"%re.escape(filename),flags=re.I)
		file_regex = re.compile(re.escape(filename),flags=re.I)

		original_time = time.time()

		while not (have_write_permission or timedout):
			try:
				folder_meta = client.metadata(request_folder)
			except dropbox.rest.ErrorResponse:
				raise IOError('Unable to get metadata for folder to check locks and flags')

			unlocked = True
			first_in_line = False
			file_exists = False

			flag_list = []

			for file_meta in folder_meta['contents']:

				basename = os.path.basename(file_meta['path'])

				if lock_regex.match(basename):
					unlocked = False
					continue

				if file_regex.match(basename):
					file_exists = True
					continue

				flagmatch = lockrequest_regex.match(basename)

				if flagmatch and not file_meta.get('is_deleted'):	
					modtime_string = file_meta['modified']
					modtime_struct = time.strptime(modtime_string,"%a, %d %b %Y %H:%M:%S +0000")
					modtime = time.mktime(modtime_struct)

					this_uid = flagmatch.group(1)

					flag_list.append((modtime,this_uid))

			flag_list.sort()

			if not flag_list:
				raise AssertionError('There should not be an empty list of flags at this point')

			first_uid = flag_list[0][1]


			first_in_line = (first_uid == client_uuid)

			if unlocked and first_in_line:
				have_write_permission = True

			else:
				elapsed_time = time.time() - original_time
				if timeout:
					if elapsed_time > timeout:
						timedout =True
				time.sleep(.5)

		if have_write_permission:
			lock_file = "_lock_%s"%filename
			lock_file_path = request_folder + '/' + lock_file
	
			try:
				client.put_file(lock_file_path,StringIO.StringIO('lock for file %s'%filename))
			except dropbox.rest.ErrorResponse:
				raise IOError('Unable to put lock')
		
		try:
			client.file_delete(flag_file_path)
		except dropbox.rest.ErrorResponse:
			out =  IOError('unable to delete lock flag')
			out.bad_lock_path = flag_file_path
			raise out
		
		return file_exists
	

	def close_all(self,):
		for file_h in self.open_files:
			file_h.close()
			
	def register_open_file(self,file_h):
		self.open_files.append(file_h)

	def release(self,path):
		client = self.client
		
		#just have to delete the right lock file
		
		request_folder,filename = path.rsplit('/',1)
		lock_string = "_lock_%s"%filename
		lock_file_path = request_folder + '/' + lock_string
		try:
			client.file_delete(lock_file_path)
		except dropbox.rest.ErrorResponse:
			raise IOError("Unable to unlock file!")
		
		
		
		
	