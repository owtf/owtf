import codecs
import os

def retreiver():
	abs_path = os.path.dirname(os.path.abspath(__file__))
	home=os.getenv("HOME")
	check="DATABASE_LOCATION:"
	path=os.path.join(abs_path,'../../profiles/general/default.cfg')
	filer=codecs.open(path)
	for index,ln in enumerate(filer):
		if check in ln:
			sc=ln.split(':')
			location=sc[1]
			location=location.lstrip('~')
			location=home+location
			return location
