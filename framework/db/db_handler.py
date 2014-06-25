#!/usr/bin/env python
'''
owtf is an OWASP+PTES-focused try to unite great tools and facilitate pen testing
Copyright (c) 2011, Abraham Aranguren <name.surname@gmail.com> Twitter: @7a_ http://7-a.org
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:
    * Redistributions of source code must retain the above copyright
      notice, this list of conditions and the following disclaimer.
    * Redistributions in binary form must reproduce the above copyright
      notice, this list of conditions and the following disclaimer in the
      documentation and/or other materials provided with the distribution.
    * Neither the name of the copyright owner nor the
      names of its contributors may be used to endorse or promote products
      derived from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY
DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

The DB stores HTTP transactions, unique URLs and more. 
'''
import os
from collections import defaultdict
from framework.lib.general import *
from framework.db import transaction_manager, url_manager, run_manager, command_register, plugin_register, report_register, debug

FIELD_SEPARATOR = ' || '

class DBHandler:
    FieldDBNames = [ 'TRANSACTION_LOG_TXT', 'RUN_DB', 'COMMAND_REGISTER', 'PLUGIN_REPORT_REGISTER', 'DETAILED_REPORT_REGISTER' ] # Field-based DBs
    LineDBNames = [ 
# Vetted URL DBs:
'ALL_URLS_DB', 'ERROR_URLS_DB', 'FILE_URLS_DB', 'IMAGE_URLS_DB', 'FUZZABLE_URLS_DB', 'EXTERNAL_URLS_DB', 'SSI_URLS_DB'
# Potential URL DBs (scraped from other tools):
, 'POTENTIAL_ALL_URLS_DB', 'POTENTIAL_ERROR_URLS_DB', 'POTENTIAL_FILE_URLS_DB', 'POTENTIAL_IMAGE_URLS_DB', 'POTENTIAL_FUZZABLE_URLS_DB', 'POTENTIAL_EXTERNAL_URLS_DB', 'POTENTIAL_SSI_URLS_DB' 
# Other DBs:
, 'TRANSACTION_LOG_HTML', 'ERROR_DB', 'SEED_DB', 'HTMLID_DB', 'DEBUG_DB', 'UNREACHABLE_DB' ] # Line-based DBs
    # DBs which have rows that could change (most are append-only):
    EditableRowDBs = [ 'RUN_DB', 'HTMLID_DB' ]

    def __init__(self, Core):
        cprint("Loading/Initialising database ..")
        self.DBNames = sorted(self.FieldDBNames + self.LineDBNames)
        self.Core = Core # Need access to reporter for pretty html trasaction log
        self.Storage = defaultdict(list)
        self.OldErrorCount = 0
    
    def GetFieldSeparator(self):
        return FIELD_SEPARATOR

    def Init(self):
        self.InitDBs()
        # Each owtf test will have a long random seed, this is used to distinguish the transaction sections in the DB
        # By having a random seed we make it considerably hard for a website to try to fool owtf to parse transactions incorrectly
        if self.IsEmpty('SEED_DB'): # Seed is global for everything in scope: URLs, Aux modules and Net plugins
            cprint("SEED DB is empty, initialising..")
            self.Add('SEED_DB', self.Core.Random.GetStr(10)) # Generate a long random seed for this test
        self.RandomSeed = self.GetRecord('SEED_DB', 0)
        self.Core.DB.Transaction.SetRandomSeed(self.RandomSeed)
        self.OldErrorCount = self.GetLength('ERROR_DB')

    def GetPath(self, DBName):
        return self.Core.Config.Get(DBName)

    def InitStore(self, Path, DBName): # The Store now works by file path: That way, we do not care about targets, etc at the DB level (Config will return the right path)
        if DBName not in self.Storage:
            self.Storage[DBName] = { Path : { 'Data' : [], 'SyncCount' : 0 } }
        if Path not in self.Storage[DBName]:
            self.Storage[DBName][Path] = { 'Data' : [], 'SyncCount' : 0 }

    def Get(self, DBName, Path = None):
        if not Path:
            Path = self.GetPath(DBName)
        #print "Get(self, "+str(DBName)+", "+str(Path)+")"
        return self.Storage[DBName][Path]

    def GetData(self, DBName, Path = None):
        return self.Get(DBName, Path)['Data']

    def GetRecord(self, DBName, Index, Path = None):
        return self.GetData(DBName, Path)[Index]

    def ModifyRecord(self, DBName, Index, Value, Path = None):
        self.GetData(DBName, Path)[Index] = Value

    def GetRecordAsMatch(self, Record, NAME_TO_OFFSET):
        Match = defaultdict(list)
        for Name, Offset in NAME_TO_OFFSET.items():
            try:
                Match[Name] = Record[Offset]
            except IndexError:
                self.Core.Error.Add("""DB.GetRecordsAsMatch ERROR: Match[Name] = Record[Offset] -> Index Error
Name="""+str(Name)+"""
Offset="""+str(Offset)+"""
Match="""+str(Match)+"""
Record="""+str(Record)+"""
""")
        return Match

    def Search(self, DBName, Criteria, NAME_TO_OFFSET, Path = None): # Returns DB Records in an easy-to-use dictionary format { 'field1' : 'value1', ... }
        Matches = []
        for Record in self.GetData(DBName, Path):
            Matched = True
            for Name, Value in Criteria.items():
                try:
                    if isinstance(Value, list):
                        if Record[NAME_TO_OFFSET[Name]] not in Value:
                            Matched = False
                    else: # Not a list
                        if Value != Record[NAME_TO_OFFSET[Name]]:
                            Matched = False
                except IndexError:
                    self.Core.Error.Add("DB.Search ERROR: The offset '"+Name+"' is undefined! NAME_TO_OFFSET="+str(NAME_TO_OFFSET)+", Record="+str(Record))
            if Matched:
                Matches.append( self.GetRecordAsMatch(Record, NAME_TO_OFFSET) )
        return Matches

    def GetSyncCount(self, DBName, Path = None):
        return self.Get(DBName, Path)['SyncCount']

    def IncreaseSync(self, DBName, Path = None):
        self.Get(DBName, Path)['SyncCount'] += 1

    def CalcSync(self, DBName, Path = None):
        self.Get(DBName, Path)['SyncCount'] = self.GetLength(DBName, Path)

    def Add(self, DBName, Data, Path = None):
        self.Get(DBName, Path)['Data'].append(Data)

    def GetLength(self, DBName, Path = None):
        return len(self.GetData(DBName, Path))

    def IsEmpty(self, DBName, Path = None):
        return self.GetLength(DBName, Path) < 1

    def InitPath(self, Path, DBName):
        self.InitStore(Path, DBName)
        self.InitDB(Path, DBName)
        self.LoadDB(Path, DBName)

    def InitDBs(self):
        #print "InitDBs.."
        for DBName in self.GetDBNames(): # Get only the DBs relevant for the type of assessment we are doing
            #print "Processing DBName="+DBName
            #self.Core.Error.FrameworkAbort("Test self.Core.Config.GetAll(DBName)="+str(self.Core.Config.GetAll(DBName)))
            for Path in self.Core.Config.GetAll(DBName): # Separate by file path value for each given DB
                #print "Before initpath for "+Path
                self.InitPath(Path, DBName)
                #print "Processing Path="+Path+", NumLines="+str(self.GetLength(DBName, Path))
                if DBName == 'HTMLID_DB' and self.IsEmpty('HTMLID_DB', Path): # There could be several HTMLID_DBs, i.e. one per URL
                    cprint("HTML ID DB is empty, initialising..")
                    self.Add('HTMLID_DB', "0", Path)

    def GetDBNames(self):
        DBNameList = []
        for DBName in self.DBNames:
            Path = self.Core.Config.Get(DBName)
            if Path: # No path set = This assessment does not need it (i.e. aux assessment does not need url db)
                DBNameList.append(DBName)
        return DBNameList

    def GetNextHTMLID(self):
        IDRecord = self.GetRecord('HTMLID_DB', 0)
        ID = str(int(IDRecord) + 1)
        self.ModifyRecord('HTMLID_DB', 0, ID)
        return ID

    def InitDB(self, Path, DBName):
        if self.Core.Config.Get('SIMULATION'):
            return None # Skip processing below, just simulating
        self.Core.CreateMissingDirs(Path)
        if not os.path.exists(Path):
            with self.Core.open(Path, 'w') as file:
                if DBName == 'TRANSACTION_LOG_HTML': # Start the HTML Transaction log:
                    self.Core.DB.Transaction.InitTransacLogHTMLIndex(file)
            
    def LoadDB(self, Path, DBName): # Load DB to memory
        if self.Core.Config.Get('SIMULATION'):
            return None # Skip processing below, just simulating
        for Line in self.Core.open(Path).read().split("\n"):
            if not Line:
                continue # Skip blank lines
            if DBName in self.FieldDBNames: # Field DBs need split to convert fields into a list
                #cprint("Field DBName: "+DBName)
                LineAsList = Line.split(FIELD_SEPARATOR)
                self.Add(DBName, LineAsList, Path) # Create list in memory for faster access
            else:
                self.Add(DBName, Line, Path) # Create list in memory for faster access
        self.CalcSync(DBName, Path) # Keep count of synced lines

    def SaveDBs(self):
        if self.Core.Config.Get('SIMULATION'):
            return None # Skip processing below, just simulating
        for DBName in self.GetDBNames(): # Get only the DBs relevant for the type of assessment we are doing
            #if DBName == 'TRANSACTION_LOG_TXT': self.Core.DB.Debug.Add('Saving DB='+DBName)
            for Path in self.Storage[DBName]: # Separate by file path value for each given DB
                #if DBName == 'TRANSACTION_LOG_TXT': self.Core.DB.Debug.Add('Saving Path='+Path+", Length="+str(self.GetLength(DBName, Path)))
                self.SaveDB(Path, DBName)

    def SaveDBLine(self, file, DBName, Line): # Contains the logic on how each line must be saved depending on the type of DB
        try:
            if DBName in self.FieldDBNames: # Field DBs need split to convert fields into a list
                file.write(FIELD_SEPARATOR.join(Line)+"\n")
            else:
                file.write(Line+"\n")
        except TypeError:
            self.Core.Error.Add("DB.SaveDBLine Type Error on DBName="+DBName+", Line="+str(Line))

    def SaveDB(self, Path, DBName):
        if self.Core.Config.Get('SIMULATION'):
            #if DBName == 'TRANSACTION_LOG_TXT': self.Core.DB.Debug.Add('DBName='+DBName+", Path="+Path+" will NOT be saved because of SIMULATION MODE")
            return None # Skip processing below, just simulating
        if self.GetLength(DBName, Path) < 1:
            #if DBName == 'TRANSACTION_LOG_TXT': self.Core.DB.Debug.Add('DBName='+DBName+", Path="+Path+" will NOT be saved because of blank DB")
            return # Avoid wiping the DB by mistake
        if DBName in self.EditableRowDBs: # DBs that are modified (Run, htmlid) need to be wiped + recreated each time
            with self.Core.open(Path, 'w') as file: # Delete + Re-create file to reflect modified last line
                for Line in self.GetData(DBName, Path): # Save all
                    self.SaveDBLine(file, DBName, Line)
        else:
            with self.Core.open(Path, 'a') as file: # Append the missing lines at the end
                #if DBName == 'TRANSACTION_LOG_TXT': self.Core.DB.Debug.Add('Saving DBName='+DBName+", Path="+Path+" from "+str(self.GetSyncCount(DBName, Path))+' until '+str(self.GetLength(DBName, Path)))
                # Only save new DB lines, instead of the full database (in the hope that it's faster)
                for Line in self.GetData(DBName, Path)[self.GetSyncCount(DBName, Path):]: 
                    self.SaveDBLine(file, DBName, Line)
        self.CalcSync(DBName, Path) # Keep count of synced lines

    def GetSeed(self):
        return self.RandomSeed

    def AddError(self, ErrorTrace):
        for Line in ErrorTrace.split("\n"):
            self.Add('ERROR_DB', Line)

    def ErrorCount(self):
        return (self.GetLength('ERROR_DB') - self.OldErrorCount)# Counts error lines but we only want to know if there has been a framework error or not

    def ErrorData(self):
        return self.GetData('ERROR_DB')[self.OldErrorCount:]
