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

MappingBase = declarative_base()

class Mappings(MappingBase):
	__tablename__ = 'Mappings'
	OWTF_code = Column(String, primary_key=True)
	OWASP_Testing_Guide_v3_num = Column(String)
	OWASP_Testing_Guide_v3_Test_Names= Column(String)
	OWASP_Testing_Guide_v4_num=Column(String)
	OWASP_Testing_Guide_v4_Test_Names=Column(String)
	NIST_control=Column(String)
	Category=Column(String)
				
path=retreiver()
#Getting the path for creating the db
path='sqlite:///'+path+'mapping.db'
engine = create_engine(path)
session = sessionmaker()
session.configure(bind = engine)
MappingBase.metadata.create_all(engine)

s = session()

title=""
abs_path = os.path.dirname(os.path.abspath(__file__))
path=os.path.join(abs_path,"../../profiles/mappings.cfg")
#profiles/mappings.cfg contains the plugin mappings to different standards.
input_file=codecs.open(path,mode="r")
lines=input_file.readlines()

for line in lines:
	titles=line.strip();
	title=titles.split(",")
	for k in range(0,7):
		if title[k]=="x":
			title[k]="Not Applicable"
	obj=Mappings(OWTF_code = title[0],
		OWASP_Testing_Guide_v3_num = title[1],
		OWASP_Testing_Guide_v3_Test_Names=title[2],
		OWASP_Testing_Guide_v4_num=title[3],
		OWASP_Testing_Guide_v4_Test_Names=title[4],
		NIST_control=title[5],
		Category=title[6])
	s.add(obj)
	line=""
	title=""
s.commit()
