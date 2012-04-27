import beaker.session

import uuid
import sys



class DrapacheSession:
	#wraps the beaker session
	#adds
	
	validate_key = str(uuid.uuid4())
	encrypt_key = str(uuid.uuid4())
	
	def __init__(self,cookie=None):
		self.session_started = False
		self.beaker_session = None
		self.beaker_dict = {}
		
		self.inner_dict = {}
		
		self.is_destroyed = False
		
		self.cookie = cookie
	
		
		
	def start(self):
		if not self.session_started:
			self.session_started = True
		
			if self.cookie is not None:
				self.beaker_dict['cookie'] = self.cookie
			
			self.beaker_session = beaker.session.CookieSession(self.beaker_dict,validate_key=self.validate_key,encrypt_key=self.encrypt_key)
						
			self.update_dict()
		
	def destroy(self):
		self.is_destroyed = True
		self.beaker_session.delete()
		self.inner_dict.clear()
		
	def get_header(self):
		#if set cookie is false, return false,
		#else return a Set-Cookie: header, with the cookie as the value
		
		if self.beaker_session is None:
			return False
		
		self.set_dict()
		
		self.beaker_session.save()
		if self.beaker_dict.get('set_cookie',False):
			return ('Set-Cookie',self.beaker_dict['cookie_out'])
		else:
			return False
			
	
	def update_dict(self):
		self.inner_dict.clear()
		self.inner_dict.update(dict((k,v) for k,v in self.beaker_session.items() if not k.startswith('_')))
		
	def set_dict(self):
		
		for k,v in self.beaker_session.items():
			if not k.startswith('_'):
				del self.beaker_session[k]
				
		for k,v in self.inner_dict.items():
			if not k in self.beaker_session:
				self.beaker_session[k] = v
		
		
	