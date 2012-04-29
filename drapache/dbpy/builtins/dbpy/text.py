import markdown
import pprint


name = 'text'

__doc__ = "Functions for working with text"

def build(env,path):
	
	
	self = env.get_new_module(path+'.'+name)
	

	@env.register(self)
	@env.privileged
	def markdown_to_html(markdown_string):
		"""
		Converts the given markdown string to html, returning it
		"""
		return markdown.markdown(markdown_string)
		
	@env.register(self)
	@env.privileged
	def pretty_print(thingy):
		"""
		Pretty prints the given `thingy`
		"""
		print "<pre>"
		printer = pprint.PrettyPrinter(indent=4)
		printer.pprint(thingy)
		print "</pre>"
		
	return self