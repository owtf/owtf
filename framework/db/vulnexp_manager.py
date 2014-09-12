from framework.db import models
from framework.config import config
import os
from framework.lib.general import cprint
import markdown
import json

class VulnexpDB(object):
    def __init__(self, Core):
        self.Core = Core
        self.VulnexpDBSession = self.Core.DB.CreateScopedSession(self.GetDBPath(), models.VulnexpBase)
 
    def GetDBPath(self):
	path = self.Core.Config.FrameworkConfigGet("EXPLANATIONS_DATABASE_PATH")
	db_name = self.Core.Config.FrameworkConfigGet("EXPLANATIONS_DATABASE")
	home = os.getenv("HOME")
	path = path.split('/',1)[1]
	path = os.path.join(home,path,db_name)
	return path

    def GetExplanation(self, plugin_code):
	session = self.VulnexpDBSession()
	explanations={}
	for i in plugin_code:
	    owtf_code=[]
	    owtf_code.append(i)
	    plugin_category = self.Core.DB.get_category(owtf_code)
	    flag=False
	    if not plugin_category:
		temp=[u'Not Applicable'] #if the category is not returned, adding the default value
		flag=True
	    category=[]
	    if not flag:
	        category.append(((plugin_category[0])[0]).encode("utf-8"))
	    if flag:
		category.append((temp[0]).encode("utf-8"))
	    #Encoding from unicode to utf-8
	    description = session.query(models.Vulnexp.desc).filter(models.Vulnexp.category.in_(category)).all()
	    description = json.loads((description[0])[0])
	    #Decoding from the Json
	    description = markdown.markdown(description)
	    #converting the markdown to html for printing in the report
	    description=description.encode("utf-8")
	    explanations[i]=description
	return explanations
