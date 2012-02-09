/*!
 * owtf JavaScript Library 
 * http://owtf.org/
 *
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
 */

$(document).ready(function() { 
	if (!DetailedReport) {//Summary Report:
		InitDB() //Working DB only initialised on summary
		ClickLinkById('tab_filter') //Enable Filter tab by default
		UpdateMemoryCounters()
		DisplayCounters(GetWorkReview(), '__SummaryCounters', '')
		DisplaySelectFilterOptions()
	}
	else { //Detailed Report
		InitDetailedReport()
		ApplyReview() //Apply reviewed plugins
		HighlightNewPlugins() //Right after loading, only once, highlight the new plugins
		ClickLinkById('tab_filter') //Enable Filter tab by default
		//ClickLinkById('filterinfo') //Click on Filter by information only
		DisplayCounters(Review[Offset], '__DetailedCounters', '')
		DisplaySelectFilterOptions()
	}
}
);

function GetSeed() {
	return GetById('seed').innerHTML
}

function GetPluginToken(PluginId) {
	return GetById('token_'+PluginId).innerHTML
}

function GetWorkReview() {
	if (!DetailedReport) {
		if (!window.Review) {
			window.Review = null
		}
		return window.Review
	}
	return window.parent.GetWorkReview()
}

function SetWorkReview(Value) {
	if (!DetailedReport) { //Review only set on summary
		window.Review = Value
		return window.Review 
	}
	return window.parent.SetWorkReview(Value)
}

function InitDB() {//Ensure all completed plugins have a review offset
	SetWorkReview(GetDB()) //Sets window.Review  -InitDB only called from summary-
	if (Review == null || !Review['__SummaryCounters']) {
		Review = {} //The review is a JSON object, which is converted into a string for storage after updating
		InitReviewCounters(Review, '__SummaryCounters')
		InitFilterOptions()
	}
}

function GetPluginInfo(PluginId) {
	var Chunks = PluginId.split(PluginDelim)
	var Plugin = { 'Group' : Chunks[0], 'Type' : Chunks[1], 'Code' : Chunks[2], 'Title' : '' }
	var CodeDiv = document.getElementById(Plugin['Code'])
	if (CodeDiv != null) Plugin['Title'] = CodeDiv.firstChild.firstChild.innerHTML
	return Plugin
}

function GetPluginField(PluginId, Field) {
	if (Review[Offset] != null && Review[Offset][PluginId] != null && Review[Offset][PluginId][Field] != null) {
		//console.log('GetPluginField => Review[' + Offset + '][' + PluginId + '][' + Field + '] = ', Review[Offset][PluginId][Field])
		return Review[Offset][PluginId][Field] //Get from review
	}
	var Plugin = GetPluginInfo(PluginId)
	if (Plugin[Field] != null) {
		return Plugin[Field] //Get from Id
	}
}

function InitDetailedReport() {
	window.Review = GetWorkReview() //Point window.Review to parent window = Counters out of whack without this
	//alert("Offet="+Offset)
	if (Review[Offset] == null) {
		Review[Offset] = {}
		InitReviewCounters(Review[Offset], '__DetailedCounters')
	}

	//console.log('InitDetailedReport -> window.AllPlugins =', window.AllPlugins)
	//console.group('InitDetailedReport -> InitPlugins')
	for (i in window.AllPlugins) {
		PluginId = window.AllPlugins[i]
		PluginToken = GetPluginToken(PluginId)
		//console.log('window.AllPlugins[' + i + ']=' + PluginId)
		if (Review[Offset][PluginId] == null) { //Review not initialised for plugin
			Review[Offset][PluginId] = { 'seen' : 'N', 'flag' : 'N', 'new' : 'Y', 'notes' : '', 'tk' : GetPluginToken(PluginId) }
			UpdateCounters( [ 'filterinfo_counter', 'filterno_flag_counter', 'filterunseen_counter' ], +1 )
		}
		else if (PluginToken != Review[Offset][PluginId].tk) {//Plugin changed (i.e. forced overwrite or grep plugin, highlight change)
			Review[Offset][PluginId].new = 'Y'
			Review[Offset][PluginId].tk = PluginToken //keep token to detect future changes
		}
		else { //Plugin has not changed, flag as not new:
			Review[Offset][PluginId].new = 'N'
		}
		PopulateComments(PluginId) //Populate comments in case of page refresh :)
		//console.log('Review[' + Offset + '][' + PluginId + ']=', Review[Offset][PluginId])
	}
	//console.groupEnd('InitDetailedReport -> InitPlugins')
	SaveDB()
}

function GetDB() {
	Storage = GetStorage() //Storage functions defined in abstraction files
	Seed = GetSeed()
	//Offset = window.Offset
	//if (Storage[Seed] == null || Storage[Seed][Offset] == null) {//DB empty
	if (Storage[Seed] == null) {//DB empty
		return {}
	}
	//return FromStr(Storage[Seed][Offset])
	return FromStr(Storage[Seed])
}

function UpdateMemoryCounters() {
	if (DetailedReport) { window.parent.UpdateMemoryCounters() } //Trigger update on parent report
	else { //Parent report only:
		GetById('js_db_size').innerHTML = GetDBUsedMemory()+' KB' //Update DB Size on screen
		GetById('total_js_db_size').innerHTML = GetStorageUsedMemory()+' KB'
	}
}

function SaveDB() {
	Storage = GetStorage()
	//alert('Storage Offset='+window.Offset)
	//Storage[GetSeed()][window.Offset] = ToStr(Review[Offset])
	//Storage[GetSeed()] = ToStr(window.Review)
	Storage[GetSeed()] = ToStr(GetWorkReview())
	//alert(ToStr(Storage))
	UpdateMemoryCounters()
}

function GetUsedMemory(DB) {
        return Math.round(ToStr(DB).length / 1024) //Return approximate KB
}

function GetDBUsedMemory() {
	return GetUsedMemory(GetStorage()[GetSeed()])
}

function GetStorageUsedMemory() {
	if(typeof _GetStorageUsedMemory== 'function') { //DB-specific implementation available (i.e. sessvars)
		return _GetStorageUsedMemory()
	}
	return GetUsedMemory(GetStorage())
}

function GetStorageMemoryPercent() {
        UsedBy100 = GetStorageUsedMemory() * 100
        if (UsedBy100 == 0) UsedBy100 = 1
        return Math.round(UsedBy100 / GetStorageSize())
}

function HidePlugin(PluginId) {
	HideDivs(new Array(PluginId))
	return SetClassNameToElems(new Array('tab_'+PluginId), '')
	//return false
}

function MarkIcon(Elem, Init) {
	if (!Init) {
		IconRow = Elem.parentNode.parentNode //Go up until the <tr> element so that we can unmark brothers and mark this one
		for (i = 0, length = IconRow.childNodes.length; i < length; i++) {
			if (IconRow.childNodes[i].className) {
				IconRow.childNodes[i].className = ''
			}
		}
	}
	Elem.parentNode.className = 'active' //Now mark as selected
}

function Rate(PluginId, Rating, Elem) {
	MarkIcon(Elem, false)
	if ('delete' == Rating) {
		Rating = 'N' //Keep the flag == 'N' for filter counter to work right
	}
	
	//console.log('Rate -> Logging Review[' + Offset + '] ..', Review[Offset])
	//console.log('Rate -> Logging Review[' + Offset + '][' + PluginId + '] ..', Review[Offset][PluginId])
	PreviousValue = Review[Offset][PluginId]['flag'] 
	//console.log('Rate -> Logging Review[' + Offset + '][' + PluginId + '][flag] ..', PreviousValue)
	NewValue = Review[Offset][PluginId]['flag'] = Rating 
	UpdatePluginCounter(PluginId, 'flag', PreviousValue, NewValue)
	SaveDB()
	ApplyReview() // Now update colours, etc
	HidePlugin(PluginId)
}

function NotBooleanStr(BooleanStr) {
	if (BooleanStr == 'Y') {
		return 'N'
	}
	return 'Y'
}

function MarkAsSeen(PluginId) {
	PreviousValue = Review[Offset][PluginId].seen
	NewValue = Review[Offset][PluginId].seen = NotBooleanStr(PreviousValue)
	UpdatePluginCounter(PluginId, 'seen', PreviousValue, NewValue)
	SaveDB()
	ApplyReview()
	HidePlugin(PluginId)
}

function BlankReview() {
	//? Review[Offset] = {}
	Review = {}
	SaveDB()
}

function GetPluginIdsForOffset(Offset) {
	PluginIds = new Array()
	for (PluginId in Review[Offset]) {
		PluginIds.push(PluginId)
	}
	return PluginIds
}

function GetPluginIdsWhereFieldMatches(Field, Value) {
	PluginIds = new Array()
	for (PluginId in Review[Offset]) {
		if (Review[Offset][PluginId][Field] == Value) {
			PluginIds.push(PluginId)
		}
	}
	return PluginIds
}

function GetSeenPlugins() {
	return GetPluginIdsWhereFieldMatches('seen', 'Y')
}

function ApplyReview() {
	if (DetailedReport) {
		SetStyleToPlugins(window.AllPlugins, '')
		SetStyleToPlugins(GetSeenPlugins(), 'line-through')
		//ApplyCounters(window.AllPlugins, 'filter', true)
	}
	else { //Summary
		//InitCounters(Prefix, '0')
		Refresh() //Normal page reload = to refresh summary + iframes
	}
}

function HighlightNewPlugins() {//Looks for differences from the previous page load to current one, highlighting new plugins shown
	//This makes it easy to see what has happened since the last refresh
	//console.log('HighlightNewPlugins -> start', 'Review[' + Offset + ']', Review[Offset])
	//console.group('Plugin loop')
	for (i=0, length = window.AllPlugins.length; i<length; i++) {
		PluginId = window.AllPlugins[i]
		//console.log('Review[' + Offset + '][' + PluginId + ']')
		//console.log(Review[Offset][PluginId])
		if (Review[Offset][PluginId].new == 'Y') {
			Tab = GetById('tab_'+PluginId)
			//Link = GetById('l'+window.AllPlugins[i])
			if (Tab != null) {
				Tab.style.backgroundColor = '#FFFFFF'//Highlighting with colours looks horrible, white background seems ok to me
				//Link.innerHTML = "->"+Link.innerHTML+"<-"
				//Tab.firstChild.innerHTML = Tab.firstChild.innerHTML+"*"
			}
		}
	}
}

function SetStyleToPlugins(PluginArray, StyleText) {
	//console.log('SetStyleToPlugins -> Review[' + Offset + ']=', Review[Offset])
	for (i=0, length = PluginArray.length; i<length; i++) {
		PluginId = PluginArray[i]
		Heading = GetById('h'+PluginId)
		StrikeIcon = GetById('l'+PluginId)
		Tab = GetById('tab_'+PluginId)
		if (Tab != null) {
			Tab.style.textDecoration = Heading.style.textDecoration = StyleText
			//alert(Tab.name)
			//Tab.style.textDecoration = StyleText
			//console.log('SetStyleToPlugins -> Review[' + Offset + '][' + PluginId + ']=')
			//console.log(Review[Offset][PluginId])
			//console.log(Review[Offset][PluginId]['flag'])
			Flag = Review[Offset][PluginId]['flag']
			Tab.parentNode.className = Flag
			RatingId = PluginId + Flag
			if (Flag != 'N' && document.getElementById(RatingId) != null) {//Check valid flag exists
				MarkIcon(GetById(RatingId), true)
			}
			if ('' == StyleText) { //Not Seen
				//Link.firstChild.innerHTML = '<img src="images/pencil.png" title="Strike-through" />'
				StrikeIcon.innerHTML = '<img src="images/pencil.png" title="Strike-through" />'
			}
			else {
				//Link.firstChild.innerHTML = '<img src="images/eraser.png" title="Unstrike-through" />'
				StrikeIcon.innerHTML = '<img src="images/eraser.png" title="Unstrike-through" />'
			}
		}
	}
}

function ClearReview() {
	if (confirm("You are going to delete all the information for this review. Are you sure?")) {
		BlankReview()
		InitDB()
		ApplyReview()
		UpdateMemoryCounters()
	}
}

function DeleteStorage() {
	if (confirm("You are going to delete all the information for ALL REVIEWS. Are you sure?")) {
		BlankReview()
		DestroyStorage()
		InitDB()
		ApplyReview()
		UpdateMemoryCounters()
	}
}

function ShowUsedMem() {
	alert('Memory in use by review storage: '+GetStorageUsedMemory()+' KB')
}

function ShowUsedMemPercentage() {
	alert('Memory in use by review storage: '+GetStorageMemoryPercent()+' %')
}

function ExportReviewAsText() {
	GetById('import_export_box').value = ToStr(GetDB()) //This way multiple import/export work on summary/detailed
	//ToStr(GetStorage()[GetSeed()]) //Get full storage, not only the window.Review (iframes loading)
	//GetById('import_export_box').value = ToStr(GetStorage()[GetSeed()]) //Get full storage, not only the window.Review (iframes loading)
	//GetById('import_export_box').value = ToStr(window.Review)
        //localStorage["AllPlugins"+Seed] //localStorage won't work in FF over file://
        //sessvars["AllPlugins"+Seed]
}

function ExportReviewAsFile() {//not working yet
	//save_content_to_file('owtf_review_export.txt', ToStr(window.Review))
	save_content_to_file('owtf_review_export.txt', ToStr(GetWorkReview()))
}

function ImportReview() {
	if (confirm('This action may erase THIS review data. Are you sure?')) {
		//window.Review = FromStr(GetById('import_export_box').value)
		SetWorkReview(FromStr(GetById('import_export_box').value))
		SaveDB()
		InitDB()
		ApplyReview()
	}
}

function GetNotesDivId(PluginId) { return 'notes_'+PluginId }

function ToggleNotesBox(PluginId) {
	var DivId = GetNotesDivId(PluginId)
	DestroyEditors(PluginId) //Destroy all other instances to keep the report lightweight
	if (GetById(DivId).style.display == 'none') {
		var Editor = CreateEditor(PluginId)
	}
	SetEditorCommentsFromStorage(PluginId)
	ToggleDiv(DivId)
}

function GetStorageComments(PluginId) {
	return Review[Offset][GetRealPluginId(PluginId)].notes
}

function SetEditorCommentsFromStorage(PluginId) {
	var EditorId = GetEditorId(PluginId)
	Data = GetStorageComments(PluginId)
	GetById(EditorId).value = Data
}

function PopulateComments(PluginId) {
	SetEditorCommentsFromStorage(PluginId)
	//$( '#' + EditorId ).val( Review[Offset][GetRealPluginId(PluginId)].notes );
	SetEditorPreview(PluginId, Data)
}

function GetEditorId(PluginId) { return 'note_text_' + PluginId }
function GetEditor(PluginId) { 
	var EditorId = GetEditorId(PluginId)
	try { //Try to get existing editor first
		var Editor = $('#' + EditorId).ckeditorGet() 
	}
	catch (e) { //Editor doesn't exist, create it and return it
		var Editor = $( '#' + EditorId).ckeditor().ckeditorGet()
	}
	return Editor
}

function SetEditorPreview(PluginId, Data) { 
	var Ids = [ PluginId ]
	if (IsReportPluginId(PluginId)) {
		Ids.push ( GetRealPluginId(PluginId) )
	}
	for (var i in Ids) {
		Id = Ids[i]
		GetById('note_preview_' + Id).innerHTML = Data.replace(/<a href/g, '<a target="_blank" href') //Open links in new tab, cumbersome otherwise ..
	}
}

function DestroyEditors(ToggledPluginId) { //Destroy all Editors to save resources
	for (var Id in CKEDITOR.instances) {
		CKEDITOR.instances[Id].destroy()
		AffectedPluginId = Id.replace('note_text_', '')
		if (AffectedPluginId != ToggledPluginId) { //Only hide other editors' divs, not the current one
			ToggleDiv(GetNotesDivId(AffectedPluginId)) //Hide affected plugin div so that things look normal
		}
	}
	//delete CKEDITOR.instances.cause
}

function CreateEditor(PluginId) { //Listen on the right events to save pen tester input as it is typed
	//Somewhat helpful links:
	//http://alfonsoml.blogspot.com/2011/03/onchange-event-for-ckeditor.html
	//http://stackoverflow.com/questions/5879832/how-to-listen-for-ckeditor-event-setdata-with-jquery
	var Editor = GetEditor(PluginId)
	//Must listen to a number of events due to lack of proper "onchange" event (somewhat surprising given the awesomeness of this editor)
	Editor.on( 'key', function() { this.fire('change') });
	Editor.on( 'paste', function() { this.fire('change') });
	Editor.on( 'currentInstance', function() { this.fire('change') });
	Editor.on( 'selectionChange', function() { this.fire('change') });
	Editor.on( 'contentDom', function() { this.fire('change') });
	Editor.on( 'blur', function() { this.fire('change') });
	Editor.on( 'change', function() { SaveComments(PluginId) });
	Editor.on( 'instanceReady', function() { this.fire('load') });
	Editor.on( 'load', function() { SetEditorCommentsFromStorage(PluginId) });
	return Editor
}

function SaveComments(PluginId) {
	//Review[Offset][GetRealPluginId(PluginId)].notes = GetById('note_text_'+PluginId).value
	//Review[Offset][GetRealPluginId(PluginId)].notes = CKEDITOR.instances['note_text_'+PluginId].getData();
	//Review[Offset][GetRealPluginId(PluginId)].notes = $( '#' + EditorId ).val();
	//Review[Offset][GetRealPluginId(PluginId)].notes = $( '#' + EditorId ).ckeditorGet().getData()
	var Data = GetEditor(PluginId).getData()
	if (Data == Review[Offset][GetRealPluginId(PluginId)].notes) { //No changes = nothing to do!
		return false
	}
        var CommentsBefore = PluginCommentsPresent(PluginId) //Comments here before = increment happened before too
	Review[Offset][GetRealPluginId(PluginId)].notes = Data
	SetEditorPreview(PluginId, Data)
        var CommentsNow = PluginCommentsPresent(PluginId)
	var CommentsCounter = GetCounterFromField('notes')
	if (!CommentsBefore && CommentsNow) { UpdateCounter( CommentsCounter, +1 ) }
	if (CommentsBefore && !CommentsNow) { UpdateCounter( CommentsCounter, -1 ) } //Decrement = one plugin less with notes
	SaveDB()
}

function SetDisplayToAllPluginTabs(Display) {
        for (var i=0, length = window.AllPlugins.length; i<length; i++) {
                var PluginId = window.AllPlugins[i]
		GetById('tab_'+PluginId).parentNode.style.display = Display
		GetById('tab_'+PluginId).className = ''
	}
}

function SetDisplayToAllTestGroups(Display) {
	Links = document.getElementsByClassName('report_index')
	for (i = 0; i < Links.length; i++) {
		Links[i].parentNode.style.display = Display
	}
}

function PluginCommentsPresent(PluginId) {
	return (Review[Offset][GetRealPluginId(PluginId)].notes.length > 0)
}

function GetCollapsedReportSize() {
	if (DetailedReport) {
		return window.parent.CollapsedReportSize
	}
	return CollapsedReportSize
}

function SelfGetDetailedReport() { //Gets the iframe from parent window
	return window.parent.document.getElementById('iframe_' + Offset) //Retrieve self from parent
}

function DetailedReportCollapse() {
	IFrame = SelfGetDetailedReport()
	IFrame.style.height = GetCollapsedReportSize()
	IFrame.className = 'iframe_collapsed' //Without horizontal scrollbar
	window.location.hash = ''
	window.parent.location.hash = ''
	ClickLinkById('tab_filter')
}

function DetailedReportAdjust() {
	IFrame = SelfGetDetailedReport()
	IFrame.style.height = IFrame.contentWindow.document.body.scrollHeight - 24 + "px"
	IFrame.className = 'iframe_collapsed' //With horizontal scrollbar (if necessary)
}

function DetailedReportExpand() {
	IFrame = SelfGetDetailedReport()
	IFrame.style.height = "100%"
	IFrame.className = 'iframe_expanded' //With horizontal scrollbar (if necessary)
}

function DetailedReportAnalyse() {
	DetailedReportExpand()
	window.parent.location.hash = 'anchor_' + Offset
}

function SelfAutoResize() {
	DetailedReportCollapse()
	DetailedReportAdjust()
}

function IsReservedOffset(Offset) { return (Offset[0] == '_' && Offset[1] == '_') }

//Below is courtesy of http://stackoverflow.com/questions/585234/how-to-read-and-write-into-file-using-javascript (not working)
function save_content_to_file(filename, content) {
    var dlg = false;
    with(document){
     ir=createElement('iframe');
     ir.id='ifr';
     ir.location='about.blank';
     ir.style.display='none';
     body.appendChild(ir);
      with(getElementById('ifr').contentWindow.document){
           open("text/plain", "replace");
           charset = "utf-8";
           write(content);
           close();
           document.charset = "utf-8";
           dlg = execCommand('SaveAs', false, filename+'.txt');
       }
       body.removeChild(ir);
     }
    return dlg;
}


//Below is courtesy of: http://stackoverflow.com/questions/1695376/msie-and-addeventlistener-problem-in-javascript
function BindEvent(El, EventName, EventHandler) {
  if (El.addEventListener){
    El.addEventListener(EventName, EventHandler, true);
  }
  else if (El.attachEvent){ //for IE compatibility
    El.attachEvent('on'+EventName, EventHandler);
  }
}
