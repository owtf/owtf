import base64
import json
import urllib2
import sys
import glob
import os
from sqlalchemy import Column
from sqlalchemy import String
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import codecs
import subprocess
from retreiver import retreiver

abs_path = os.path.dirname(os.path.abspath(__file__))
file_path=os.path.join(abs_path,"../../framework/scripts/commit-hash")
#getting the old commit-hash for comparison
old_hash=""
ink = codecs.open(file_path,mode='r')
hash=ink.readlines()
for ln in hash:
    old_hash+=ln

new_hash=""
p = subprocess.Popen("git ls-remote https://github.com/owtf/boilerplate-templates.git | grep HEAD | awk '{print $1}' ", shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
#Getting the latest commit hash from github
for line in p.stdout.readlines():
    new_hash+=line
retval = p.wait()

if new_hash!=old_hash:
    os.remove(file_path)
    file=codecs.open(file_path,'w')
    file.write(new_hash)
    #Updating the file with latest commit hash
    file.close


    GITHUB_REPOS_API_BASE_URL = 'https://api.github.com/repos/'
    def write_file(item, dir_name):
        name = item['name']
        res = urllib2.urlopen(item['url']).read()
        coded_string = json.loads(res)['content']
        contents = base64.b64decode(coded_string)
        print os.path.join(dir_name, name)
        f = open(os.path.join(dir_name, name), 'w')
        f.write(contents)
        f.close()

    def write_files(url, dir_name, recursive=True):
        print 'url', url
        os.makedirs(dir_name)
        github_dir = json.loads(urllib2.urlopen(url).read())
        for item in github_dir:
            if item['type'] == 'file':
                write_file(item, dir_name)
            elif item['type'] == 'dir':
                write_files(item['url'], dir_name=os.path.join(dir_name, item['name']))


    if __name__ == '__main__':
        args = dict(enumerate(sys.argv))
        path = 'owtf/boilerplate-templates/_posts'
        #Cloning a particular sub directory from git (for DB updation)
        path = path.split('/')
        new_dir_name = path[-1]
        if os.path.exists(new_dir_name):
            raise 'Directory', new_dir_name, 'already exists'

        # use contents api
        path.insert(2, 'contents')
        path = '/'.join(path)
        recursive = eval(args.get(2)) if args.get(2) else True
        write_files(GITHUB_REPOS_API_BASE_URL + path, new_dir_name, recursive=recursive)


    ExpBase = declarative_base()
    class Vulnexp(ExpBase):
    	__tablename__ = 'Vulnexp'
    	Title = Column(String, primary_key=True)
	Desc = Column(String)
	Category=Column(String)

	path=retreiver()
	#getting the path for db creation
	path='sqlite:///'+path+'vulnexp.db'
	engine = create_engine(path)
	session = sessionmaker()
	session.configure(bind = engine)
	ExpBase.metadata.create_all(engine)
	s = session()

	texto=""
	title=""

	os.chdir("_posts")
	for file in glob.glob("*.md"):
	    inp=codecs.open(file,mode="r")
	    i=1
	    tect=inp.readlines()
	    for line in tect:
	    	if i==6:
	    	    lock=line.strip()
		if i==3:
 	            title=line.strip()
	        if i>7:
	            texto+=line
		i=i+1

	    title2=title.split(":")
	    vuln = {'Title': title2[1], 'Desc':texto }
	    vuln_desc = json.dumps(texto)
	    obj = Vulnexp(Title = vuln['Title'],Desc=vuln_desc,Category=lock)
	    s.add(obj)
	    line=""
	    title=""
	    texto=""
	s.commit()
else:
    print("No update necessary")
