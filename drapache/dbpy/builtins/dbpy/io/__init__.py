import file
import jsonfile

submodules = [file,jsonfile]

name = 'io'

def build(env,path):
	
	
	self = env.get_new_module(path+'.'+name)
	
	for module in submodules:
		setattr(self,module.name,module.build(env,path+'.'+name))
		
	return self	
	