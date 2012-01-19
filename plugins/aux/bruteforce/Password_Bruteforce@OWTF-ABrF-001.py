"""
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
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

"""
DESCRIPTION = "Password Bruteforce Testing plugin"
BRUTEFORCER = [ 'hydra' ]
CATEGORIES = [ 'RDP', 'LDAP2', 'LDAP3', 'MSSQL', 'MYSQL', 'CISCO', 'CISCO-ENABLE', 'CVS', 'Firebird', 'FTP', 'FTPS', 'HTTP-PROXY', 'ICQ', 'IMAP', 'IRC', 'NCP', 'NNTP', 'ORACLE-LISTENER', 'ORACLE-SID', 'PCANYWHERE', 'PCNFS', 'POP3', 'POSTGRES', 'REXEC', 'RLOGIN', 'RSH', 'SIP', 'SMB', 'SMTP', 'SNMP', 'SOCKS5', 'SSH', 'SVN', 'TEAMSPEAK', 'TELNET', 'VMAUTHD', 'VNC', 'XMPP' ]
def run(Core, PluginInfo):
	#Core.Config.Show()
	Content = DESCRIPTION + " Results:<br />"
	for Args in Core.PluginParams.GetArgs( { 
'Description' : DESCRIPTION,
'Mandatory' : { 
		'RHOST' : Core.Config.Get('RHOST_DESCRIP'), 
		'RPORT' : Core.Config.Get('RPORT_DESCRIP'), 
		'CATEGORY' : 'Category to use (i.e. '+', '.join(sorted(CATEGORIES))+')'
	      }, 
'Optional' : {
		'BRUTEFORCER' : 'Bruteforcer to use (i.e. '+', '.join(sorted(BRUTEFORCER))+')',
		'ONLINE_USER_LIST' : Core.Config.Get('ONLINE_USER_LIST_DESCRIP'),
		'ONLINE_PASSWORD_LIST' : Core.Config.Get('ONLINE_PASSWORD_LIST_DESCRIP'),
		'THREADS' : Core.Config.Get('THREADS_DESCRIP'),
		'RESPONSE_WAIT' : Core.Config.Get('RESPONSE_WAIT_DESCRIP'),
		'CONNECT_WAIT' : Core.Config.Get('CONNECT_WAIT_DESCRIP'), 
		'REPEAT_DELIM' : Core.Config.Get('REPEAT_DELIM_DESCRIP')
	     } }, PluginInfo):
		Core.PluginParams.SetConfig(Args)
		#print "Args="+str(Args)
		Content += Core.PluginHelper.DrawCommandDump('Test Command', 'Output', Core.Config.GetResources('PassBruteForce_'+Args['BRUTEFORCER']+"_"+Args['CATEGORY']), PluginInfo, "") # No previous output
	return Content

