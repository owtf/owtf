from framework.db import models
from framework.config import config
from framework.lib.general import cprint
import os

class MappingDB(object):
    def __init__(self, Core):
        self.Core = Core
        self.MappingDBSession = self.Core.DB.CreateScopedSession(self.Core.Config.FrameworkConfigGetDBPath("MAPPINGS_DB_PATH"), models.MappingBase)
        self.LoadMappingDBFromFile(self.Core.Config.FrameworkConfigGet("DEFAULT_MAPPING_PROFILE"))
        
    def LoadMappingDBFromFile(self, file_path): # This needs to be a list instead of a dictionary to preserve order in python < 2.7
        cprint("Loading Mapping from: " + file_path + " ..")
        mapping = self.GetMappingFromFile(file_path)
        session = self.MappingDBSession()
        for owtfcode, owaspv3, v3_names, owaspv4, v4_names, nist, category in mapping:
            if not session.query(models.Mapping).filter_by(owtf_code = owtfcode, owasp_guide_v3_num = owaspv3, owasp_guide_v3_names = v3_names, owasp_guide_v4_num = owaspv4, owasp_guide_v4_names = v4_names, nist_control = nist, category = category ).all():
                session.add(models.Mapping(owtf_code = owtfcode, owasp_guide_v3_num = owaspv3, owasp_guide_v3_names = v3_names, owasp_guide_v4_num = owaspv4, owasp_guide_v4_names = v4_names, nist_control = nist, category = category))
        session.commit()
        session.close()
        
    def GetMappingFromFile(self, mapping_file):
        mapping = []
        ConfigFile = self.Core.open(mapping_file, 'r').read().splitlines() # To remove stupid '\n' at the end
        for line in ConfigFile:
            if '#' == line[0]:
                continue # Skip comment lines
            try:
                owtfcode, owaspv3, v3_names, owaspv4, v4_names, nist, category = line.split('_____')        
                mapping.append((owtfcode, owaspv3, v3_names, owaspv4, v4_names, nist, category))
            except ValueError:
                cprint("ERROR: The delimiter is incorrect in this line at Mapping File: "+str(line.split('_____')))
        return mapping
    
    def GetCategory(self, plugin_code):
	session = self.MappingDBSession()
	category = session.query(models.Mapping.category).filter(models.Mapping.owtf_code.in_(plugin_code)).all()
	#Getting the corresponding category back from db	
	return category
