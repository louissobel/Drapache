import markdown
import pprint


name = 'text'

def build(env,path):
	
	
	self = env.get_new_module(path+'.'+name)
	

	@env.register(self)
	@env.privileged
	def markdown_to_html(markdown_string):
		return markdown.markdown(markdown_string)
		
	@env.register(self)
	@env.privileged
	def pretty_print(thingy,pre=True):
		"""
		Pretty prints the given thingy
		"""
		print "<pre>"
		printer = pprint.PrettyPrinter(indent=4)
		printer.pprint(thingy)
		print "</pre>"
		
	return self