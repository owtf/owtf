"""For retreving Database path from framework/config/framework_config.cfg"""
import codecs
import os

def retreiver():
	abs_path = os.path.dirname(os.path.abspath(__file__))
	home=os.getenv("HOME")
	check="MAPPINGS_DATABASE_PATH:"
	path=os.path.join(abs_path,'../../framework/config/framework_config.cfg')
	filer=codecs.open(path)
	for index,ln in enumerate(filer):
		if check in ln:
			sc=ln.split(':')
			location=sc[1]
			location=location.lstrip('~')
			location=home+location
			return location
