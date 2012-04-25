"""
The index auto generator
"""
import os
import jinja2
from jinja2 import Environment,PackageLoader
import dbapi.jinja



def get_index_file(file_list,folder_path,client):
	
	
	"""
	The index auto generator
	"""

	DEFAULT_INDEX = """
	<html>

		<head>
		<title>Index - {{path}}</title>
		</head>


		<body>

			<h1> Index for {{path}} </h1>

			{% for file in files %}
				<a href="{{file}}">{{file}}</a><br>
			{% endfor %}

		</body>

	</html>
	"""

	files = []
	for filemeta in file_list:
		file_name = os.path.basename(filemeta['path'])
		if filemeta['is_dir']:
			file_name = file_name + '/'
		files.append(file_name)

	dropbox_env = Environment(loader=dbapijinja.DropboxLoader(client,'/_templates'))

	try:
		custom_index_template = dropbox_env.get_template('index.html')
		return custom_index_template.render(files=files,path=folder_path)

	except jinja2.TemplateNotFound:
		index_template = jinja2.Template(DEFAULT_INDEX)
		return index_template.render(files=files,path=folder_path)
