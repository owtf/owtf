/*!
 * owtf JavaScript Library 
 * http://owtf.org/
 */

/*
	This file handles the report building from the data in the review
*/

$(document).ready(function() {
	GetSkinCookieAndApply(); //change the skin based on the cookie value
	 //Take weights from parent window:
		window.SeverityWeightOrder = window.parent.SeverityWeightOrder
		window.PassedTestIcons = window.parent.PassedTestIcons
	}
);

function IsReportPluginId(PluginId) {
	return PluginId != GetRealPluginId(PluginId)	
}

function GetRealPluginId(PluginId) { //Clean fake Plugin Id for reporting (to avoid interferring with review)
	return PluginId.replace(REPORT_PREFIX, '') 
}

function AppendPluginToReport(Offset, PluginId) {
	//DestroyEditors(Offset, PluginId) //Destroy all other instances to avoid CKEditor errors
	//Plugin has notes + displayed now
	//NotesTextArea = GetById('note_text_'+ Offset + "_"+ PluginId)
	//NotesTextArea.value = NotesPreview.innerHTML
	//Content +=  '<div id="rep__' + PluginId + '">' + NotesPreview.parentNode.innerHTML + '</div>'
	//Super-dirty but easiest way to avoid code-duplication for now :P
	//NotesPreview.parentNode.innerHTML = '<div id="del__' + PluginId + '"></div>' 
	NotesPreview = GetById('note_preview_'+ Offset + "_" + PluginId)
	IdReplace = new RegExp(PluginId, "g");
	return '<div>' + NotesPreview.parentNode.innerHTML.replace(IdReplace, REPORT_PREFIX + PluginId) + '</div>' //Make all element ids different via replace
}

function CanReport(Offset, PluginId) {
	Plugin = GetPluginInfo(PluginId)
	Tab = GetById('tab_' + PluginId).parentNode
	CodeDiv = GetById(Plugin['Code'])
	//console.log('CanReport => Tab.style.display=', Tab.style.display, 'Plugin=', Plugin, 'CodeDiv.style.display=', CodeDiv.style.display)
	return (PluginCommentsPresent(Offset, PluginId) && Tab.style.display != 'none' && CodeDiv.style.display != 'none')
}

function GetHTMLReportIntro(Offset) {
	TargetStr = escape(Offset).replace('p', ':').replace('i','').replace("_",".")
	TargetURL = document.getElementById("offset_"+Offset)
	if (TargetURL != null) {
		TargetStr = TargetURL.innerHTML //Copy link from top table if present ;)
	}
	return 'Review Report for:' + TargetStr + ''
}

function IsPassedTest(Offset, PluginId) {
	//console.log('IsPassedTest(' + PluginId + ')=', InArray(GetPluginField(Offset, PluginId, 'flag'), window.PassedTestIcons))
	return InArray(GetPluginField(Offset, PluginId, 'flag'), window.PassedTestIcons)
}

function PassedTestProcessPlugin(Offset, PluginId) {
	//console.log('PassedTestProcessPlugin(PluginId)=', PluginId, 'notes=', GetPluginField(Offset, PluginId, 'notes'))
	return GetPluginField(Offset, PluginId, 'notes')
}

function PassedTestProcessCode(Offset, LastPluginIdForCode, PluginContent) {
	return '<li>' + GetPluginField(Offset, LastPluginIdForCode, 'Title') + '</li>' + PluginContent 
}

function GetHTMLPassedTestsByCode(Offset, Stats) {
	var Content = ''
	var Data = ReportPluginsByCode(Offset,  { 
			  'ProcessPluginIF' : 'IsPassedTest(Offset, PluginId)' 
			, 'ProcessPluginFunction' : 'PassedTestProcessPlugin(Offset, PluginId)' 
			, 'ProcessCodeFunction' : 'PassedTestProcessCode(Offset, LastPluginIdForCode, PluginContent)' 
		} )
	if (Data['Count'] == 0) {
		Content += 'no tests passed'
	}
	else {
		Content += '<p>The following tests did not identify vulnerabilities in the target system:</p>'
		Content += '<ul class="report_list">'
		Content += Data['Content']
		Content += '</ul>'
	}
	Stats['Passed'] = Data['Count']
	return Content
}

function IsFinding(Offset, PluginId, Severity) {
	//console.log('IsPassedTest(' + PluginId + ')=', InArray(GetPluginField(Offset, PluginId, 'flag'), window.PassedTestIcons))
	var Flag = GetPluginField(Offset, PluginId, 'flag')
	return Flag == Severity && InArray(Flag, window.SeverityWeightOrder)
}

function FindingProcessPlugin(Offset, PluginId, Severity) {
	//console.log('PassedTestProcessPlugin(PluginId)=', PluginId, 'notes=', GetPluginField(Offset, PluginId, 'notes'))
	return GetPluginField(Offset, PluginId, 'notes')
}

function FindingProcessCode(Offset, LastPluginIdForCode, PluginContent, Severity) {
	if (PluginContent.length == 0) {
		PluginContent = '<span class="text-warning"> No notes found for any plugin under this category</span>'
	}
	return '<li>' + GetPluginField(Offset, LastPluginIdForCode, 'Title') + ' - ' + GetSeverityName(Severity) + " "+ GetSeverityIcon(Severity) + '</li>' + PluginContent
}

function GetSeverityName(Severity) {
	return $('#filter' + Severity).data("originalTitle")
}

function GetSeverityIcon(Severity) {
	return "<i class='"+ $('#filter' + Severity).children().first().attr("class") +"'></i>"
}

function GetHTMLFindingsBySeverityAndCode(Offset, Stats) {
	//console.log('(FindingsBySev) Index=', Index)
	var Content = ''
	Content += '<ol class="finding_severity">'
	var TotalCount = 0
	for (i in window.SeverityWeightOrder) {
		var Severity = window.SeverityWeightOrder[i]
		var SeverityContent = '<li>' + GetSeverityIcon(Severity) + " " +GetSeverityName(Severity) + '</li>'
	var Data = ReportPluginsByCode(Offset, { 
		'ProcessPluginIF' : 'IsFinding(Offset, PluginId, "' + Severity + '")' //Limit processing by severity each time
		, 'ProcessPluginFunction' : 'FindingProcessPlugin(Offset, PluginId, "' + Severity + '")'
		, 'ProcessCodeFunction' : 'FindingProcessCode(Offset, LastPluginIdForCode, PluginContent, "' + Severity + '")' 
		} )
	Stats[Severity] = Data['Count']
	TotalCount += Data['Count']
	if (Data['Count'] != 0) {
		SeverityContent += '<ul class="finding">'
		SeverityContent += Data['Content']
		SeverityContent += '</ul>'
		Content += SeverityContent
		}
	}
	Content += '</ol>'
	if (TotalCount == 0) {
		Content += '<p>no findings were found</p>'
	}
	return Content
}

function GetHTMLRenderStats(Offset, Stats) {
	var Content = ''
	Stats['Unrated'] = GetPluginIdsWhereFieldMatches(Offset, 'flag', 'N').length
	Content += '<ul class="report_list">'
	for (Item in Stats) {
		Count = Stats[Item]
		if (Item == 'Passed') {
			DisplayName = "Passed Tests"
		}
		else if (Item == 'Unrated') {
			DisplayName = "Unrated Tests"
		}
		else { //Severity: Get Name
			DisplayName = GetSeverityIcon(Item) +" "+GetSeverityName(Item)
		}
		Content += '<li>' + DisplayName + ': ' + Count + '</li>'
	}
	Content += '</ul>'
	return Content
}

function BuildReportBySeverityAndCode(Offset, Report) {
	GetById(Offset+'__rep__intro').innerHTML = GetHTMLReportIntro(Offset)
	var Stats = {}
	GetById(Offset+'__rep__passed').innerHTML = GetHTMLPassedTestsByCode(Offset, Stats)
	GetById(Offset+'__rep__findings').innerHTML = GetHTMLFindingsBySeverityAndCode(Offset, Stats)
	GetById(Offset+'__rep__unrated').innerHTML = 'not implemented yet'
	//Stats are set in the same loop by previous function calls: Must be done at the end
	GetById(Offset+'__rep__stats').innerHTML = GetHTMLRenderStats(Offset, Stats) 
//&& CanReport(Offset, PluginId) 
}

function ReportPluginsByCode(Offset, Options) {
	var Count = 0
	var Content = ''
	for (i in window.ReportsInfo[Offset].AllCodes) {
		Code = window.ReportsInfo[Offset].AllCodes[i]
		var PluginContent = ''
		var PluginCount = 0
		for (i in window.ReportsInfo[Offset].AllPlugins) {
			var PluginId = window.ReportsInfo[Offset].AllPlugins[i]
			if (GetPluginField(Offset, PluginId, 'Code') == Code && eval(Options['ProcessPluginIF'])) {
				LastPluginIdForCode = PluginId
				PluginContent += eval(Options['ProcessPluginFunction'])
				PluginCount += 1
			}
		}
		if (PluginCount > 0) {
			Content += eval(Options['ProcessCodeFunction'])	
			Count += PluginCount
		}
	}
	return { 'Content' : Content, 'Count' : Count }
}

function ToggleReportMode(Offset) {
	DetailedReportAnalyse(Offset)
	ToggleDivs( [ 'subreport_'+Offset, 'generated_report_'+Offset ] )
	Report = GetById('generated_report_'+Offset)
	if (Report.style.display != 'none' && confirm('This can take a few seconds or minutes depending on the report size. Generate report?')) { //Display report
		window.ReportMode = true
		BuildReportBySeverityAndCode(Offset, Report)
		//AffectedPlugins = BuildReportByCode(Report)
		//Report.innerHTML += GetNoMatchesFoundMessage(AffectedPlugins)
	}
	else { //Restore Note boxes .. 
		window.ReportMode = false
		//RestoreOriginalReport(Report)
	}
	/*
		0) Set ReportMode to true
		1) Hide everything
		2) Create Report Div
		3) Copy innerHTML from notes_preview
		4) Remove innerHTML from notes_preview  

		Undo:
		0) On any filter or undo filter => If ReportMode == true
		1) Copy notes_preview from report div back to notes_preview
		2) Destroy report div
	*/
	//SetDisplayToAllPluginTabs('none') //Hide all plugin tabs
	//SetDisplayToDivs(window.AllPlugins, 'none')//Hide all plugin divs
	//SetDisplayToAllTestGroups('none') //Hide all index divs
	//SetDisplayToAllPluginTabs('none') //Hide all plugin tabs (it's confusing when you filter and see flags you did not filter by)
	//AffectedPlugins = UnfilterPluginsWhereCommentsPresent(Offset)
	//SetDisplayUnfilterPlugins('')
}
/*var NumPassed = 0
for (i in window.PassedTestIcons) {
	var Flag = window.PassedTestIcons[i]
	NumPassed += GetFlagCount(Flag)
}*/
