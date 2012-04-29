import drapache.dbpy.builtins.dbpy as dbpy


import re
import inspect	
import pprint
		
import json		

def get_help_hash(module):
	
	children = []
	doc = {'type':'module','name':module.name,'children':children,'doc':module.__doc__}
		
	if hasattr(module,'submodules'):
		for child in module.submodules:
			
			if hasattr(child,'get_doc'):
				child_hash = child.get_doc()
			else:
				child_hash = get_help_hash(child)
			
			children.append(child_hash)
		
	module_code = inspect.getsource(module)
	
	#go through, finding attributes and functions
	
	mode = 'looking'
	cur_hash = {}
	cur_doc = []
	
	
	target = None
	
	attributes = []
	functions = []
	
	attribute_pattern = re.compile('#DOC:(.+)')
	function_pattern = re.compile('@env.register')
	
	def_pattern = re.compile('def (.+?):')
	
	for line in module_code.split('\n'):
		line = line.strip()
		
		#print "%s === %s" % (mode,line)
		
		if mode == 'looking':
			
			attr_match = attribute_pattern.match(line)
			if attr_match:
				cur_hash['type'] = 'attribute'
				cur_hash['name'] = attr_match.group(1)
				cur_hash['children'] = []
				target = attributes
				mode = 'doc_expecting'
				
			else:
				function_match = function_pattern.match(line)
				if function_match:
					cur_hash['type'] = 'function'
					cur_hash['children'] = []
					target = functions
					mode = 'def_expecting'
		
		elif mode == 'def_expecting':
			def_match = def_pattern.match(line)
			if def_match:
				mode = 'doc_expecting'
				cur_hash['name'] = def_match.group(1)
				
		elif mode == 'doc_expecting':
			if '"""' in line:
				mode = 'doc_sucking'
			function_match = function_pattern.match(line)
			if function_match:
				cur_hash['type'] = 'function'
				cur_hash['children'] = []
				target = functions
				mode = 'def_expecting'
		
		elif mode == 'doc_sucking':
			if '"""' in line:
				cur_hash['doc'] = ' '.join(cur_doc)
				target.append(cur_hash)
				cur_hash = {}
				cur_doc = []
				mode = 'looking'
			else:
				cur_doc.append(line)
		
	children.extend(attributes)
	children.extend(functions)
	
	return doc
		
if __name__ == "__main__":
	print json.dumps(get_help_hash(dbpy))