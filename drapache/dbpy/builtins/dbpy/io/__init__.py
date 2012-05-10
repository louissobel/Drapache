import file
import json_dbpy

submodules = [file,json_dbpy]

name = 'io'

__doc__ = "Module for file and json dropbox read/write operations"

def build(env,path):
	
	
	self = env.get_new_module(path+'.'+name)
	
	for module in submodules:
		setattr(self,module.name,module.build(env,path+'.'+name))
		
	return self	
	