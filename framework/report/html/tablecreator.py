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

The tab module simplifies tab creation via CSS
'''
from framework.lib.general import *
from collections import defaultdict
import cgi

class TableCreator:
	def __init__(self, Renderer, Attribs = {}):
		self.Renderer = Renderer
		self.Attribs = Attribs
                self.CSSAltClass = { True : ' class="alt"', False : '' }
                self.RowAltTracker = defaultdict(list)
		self.Rows = []

        def InitRowAlt(self, NumItems, RowNum = None):
                if None == RowNum:
                        Index = NumItems
                        self.RowAltTracker[Index] = False # Init to alternative row = False when headers are drawn

        def GetRowAlt(self, NumItems, RowNum = None):
                if None != RowNum:
                        Modulus = int(RowNum) % 2
                        IsZero = (Modulus == 0)
                        return self.CSSAltClass[IsZero]
                IsAlt = False
                if self.RowAltTracker[NumItems]:
                        IsAlt = True
                return self.CSSAltClass[IsAlt]

        def UpdateRowAlt(self, NumItems, RowNum = None):
                if None != RowNum:
                        return None
                if self.RowAltTracker[NumItems]:
                        IsAlt = False
                else:
                        IsAlt = True
                self.RowAltTracker[NumItems] = IsAlt

        def DrawTableRow(self, ColumnList, Header = False, RowAttribs = {}, RowNum = None):
                NumItems = len(ColumnList)
                if Header:
                        self.InitRowAlt(NumItems, RowNum)
                        PadS = "<th>"
                        PadF = "</th>"
                else:
                        PadS = "<td"+self.GetRowAlt(NumItems, RowNum)+">"
                        #PadS = "<td>"
                        PadF = "</td>"
                        self.UpdateRowAlt(NumItems, RowNum)
                CellS = PadF+PadS
		#print "self.Renderer.GetAttribsAsStr(RowAttribs)="+str(self.Render.GetAttribsAsStr(RowAttribs))
                return "<tr"+self.Renderer.GetAttribsAsStr(RowAttribs)+">"+PadS+CellS.join(ColumnList)+PadF+"</tr>"#.replace(PadF, "&nbsp;"+PadF) # Replace blanks by space
                #return "<tr"+self.GetRowAlt(NumItems, RowNum)+">"+PadS+CellS.join(ColumnList)+PadF+"</tr>"

	def EscapeCells(self, CellList):
		CleanList = []
		for Cell in CellList:
			CleanList.append(cgi.escape(Cell))
		return CleanList
	
	def CreateRow(self, ColumnList, Header = False, RowAttribs = {}, RowNum = None):
		self.Rows.append(self.DrawTableRow(ColumnList, Header, RowAttribs, RowNum))

	def CreateCustomRow(self, HTML):
		self.Rows.append(HTML)

	def GetNumRows(self):
		return len(self.Rows)

	def Render(self):
		return """
<table"""+self.Renderer.GetAttribsAsStr(self.Attribs)+""">
	"""+"\n".join(self.Rows)+"""
</table>"""

