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

"""
DESCRIPTION = "Spear Phising Testing plugin"
def run(Core, PluginInfo):
	#Core.Config.Show()
	Content = DESCRIPTION + " Results:<br />"
	for Args in Core.PluginParams.GetArgs( { 
'Description' : DESCRIPTION,
'Mandatory' : { 
		'EMAIL_TARGET' : Core.Config.Get('EMAIL_TARGET_DESCRIP'),
		'EMAIL_FROM' : Core.Config.Get('EMAIL_FROM_DESCRIP'),
		'PHISHING_PAYLOAD' : Core.Config.Get('PHISHING_PAYLOAD_DESCRIP'),
		'SET_EMAIL_TEMPLATE' : Core.Config.Get('SET_EMAIL_TEMPLATE_DESCRIP'),
		'SMTP_LOGIN' : Core.Config.Get('SMTP_LOGIN_DESCRIP'),
		'SMTP_PASS' : Core.Config.Get('SMTP_PASS_DESCRIP'),
		'SMTP_HOST' : Core.Config.Get('SMTP_HOST_DESCRIP'),
		'SMTP_PORT' : Core.Config.Get('SMTP_PORT_DESCRIP'),
		'EMAIL_PRIORITY' : Core.Config.Get('EMAIL_PRIORITY_DESCRIP'),
		'PDF_TEMPLATE' : Core.Config.Get('PDF_TEMPLATE_DESCRIP'),
		'MSF_LISTENER_PORT' : Core.Config.Get('MSF_LISTENER_PORT_DESCRIP'),
		'MSF_LISTENER_SETUP' : Core.Config.Get('MSF_LISTENER_SETUP_DESCRIP'),
		'ATTACHMENT_NAME' : Core.Config.Get('ATTACHMENT_NAME_DESCRIP'),
		'PHISING_SCRIPT_DIR' : Core.Config.Get('PHISING_SCRIPT_DIR_DESCRIP')
	      },
'Optional' : {
		'REPEAT_DELIM' : Core.Config.Get('REPEAT_DELIM_DESCRIP')
	     } }, PluginInfo):
		Args['ATTACHMENT_NAME'] = Args['ATTACHMENT_NAME']+"_"+Args['PHISHING_PAYLOAD']+"-"+Args['SET_EMAIL_TEMPLATE']
		Core.PluginParams.SetConfig(Args) # Only now, after modifying ATTACHMENT_NAME, update config
		#print "Args="+str(Args)
		Content += Core.PluginHelper.DrawCommandDump('Test Command', 'Output', Core.Config.GetResources('SendPhisingAttackviaSET'), PluginInfo, Content)
	return Content

