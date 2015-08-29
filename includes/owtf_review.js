/*!
 * owtf JavaScript Library 
 * http://owtf.org/
 */

$(document).ready(function() { 

	InitAllTheWorld()
	//InitDB() //Working DB only initialised on summary
	//DisplayCounters(GetWorkReview(), "__SummaryCounters", '')
	//DisplaySelectFilterOptions()

}
);

function InitAllTheWorld()
{
	InitDB() //Working DB only initialised on summary
	InitFilterOptions()
	DisplaySelectFilterOptions()
	
	//Initialize all Detailed Reports
	 for (var i = 0; i < window.AllTargets.length; i++)
		 {
		 	//ReportID = AllTargets[i]
			//InitDetailedReport(ReportID)
			//ApplyReview( ReportID ) //Apply reviewed plugins
			//HighlightNewPlugins( ReportID ) //Right after loading, only once, highlight the new plugins
			//ClickLinkById('filterinfo') //Click on Filter by information only
			
		 }
	
	DisplayCounters(GetWorkReview(), "__SummaryCounters", '')

	
}

function GetSeed() {
	return GetById('seed').innerHTML
}

function GetPluginToken(Offset,PluginId) {
	var element = GetById('token_'+Offset+"_"+PluginId)
	if (element == null) 
		{ 
			innerHTML = ""
			alert('token_'+Offset+"_"+PluginId+" is null")
		}
	else innerHTML=GetById('token_'+Offset+"_"+PluginId).innerHTML
	return innerHTML
}

function GetWorkReview() {
		if (!window.Review) {
			window.Review = {}
		}
		return window.Review
}

function SetWorkReview(Value) {
		window.Review = Value
		return window.Review 
}

function InitDB() {//Ensure all completed plugins have a review offset
	SetWorkReview(GetDB()) //Sets window.Review  -InitDB only called from summary-
	if (Review == null) {
		Review = {} //The review is a JSON object, which is converted into a string for storage after updating
		InitReviewCounters(Review, '__SummaryCounters')
		InitFilterOptions()
	}
}

function GetPluginInfo(Offset, PluginId) {
	var Chunks = PluginId.split(PluginDelim)
	var Plugin = { 'Group' : Chunks[0], 'Type' : Chunks[1], 'Code' : Chunks[2], 'Title' : '' }
	var CodeDiv = document.getElementById(Offset +"_"+Plugin['Code']+"_title")
	if (CodeDiv != null) Plugin['Title'] = CodeDiv.innerHTML
	return Plugin
}

function GetPluginField(Offset, PluginId, Field) {
	if (Review[Offset] != null && Review[Offset][PluginId] != null && Review[Offset][PluginId][Field] != null) {
		//console.log('GetPluginField => Review[' + Offset + '][' + PluginId + '][' + Field + '] = ', Review[Offset][PluginId][Field])
		return Review[Offset][PluginId][Field] //Get from review
	}
	var Plugin = GetPluginInfo(Offset, PluginId)
	if (Plugin[Field] != null) {
		return Plugin[Field] //Get from Id
	}
}

function InitDetailedReport(Offset) {
	window.Review = GetWorkReview() //Point window.Review to parent window = Counters out of whack without this
	
	if (!Review["__SummaryCounters"]) {
		InitReviewCounters(Review, "__SummaryCounters")
	}
	
	if ( Review[Offset] == null) {
		Review[Offset] = {}
		InitReviewCounters(Review[Offset], "__"+ Offset + "Counters")
	}
	
	
	

	//console.log('InitDetailedReport -> window.ReportsInfo[Offset].AllPlugins =', window.ReportsInfo[Offset].AllPlugins)
	//console.group('InitDetailedReport -> InitPlugins')
	for (i in window.ReportsInfo[Offset].AllPlugins) {
		PluginId = window.ReportsInfo[Offset].AllPlugins[i]
		PluginToken = GetPluginToken(Offset, PluginId)
		//console.log('window.ReportsInfo[Offset].AllPlugins[' + i + ']=' + PluginId)
		if (Review[Offset][PluginId] == null) { //Review not initialised for plugin
			Review[Offset][PluginId] = { 'seen' : 'N', 'flag' : 'N','fav' : 'N', 'new' : 'Y', 'notes' : '', 'tk' : GetPluginToken(Offset, PluginId) }
			UpdateCounters( Offset, [ 'filterinfo_counter', 'filterno_flag_counter', 'filterunseen_counter' ], +1 )
		}
		else if (PluginToken != Review[Offset][PluginId].tk) {//Plugin changed (i.e. forced overwrite or grep plugin, highlight change)
			Review[Offset][PluginId].new = 'Y'
			Review[Offset][PluginId].tk = PluginToken //keep token to detect future changes
		}
		else { //Plugin has not changed, flag as not new:
			Review[Offset][PluginId].new = 'N'
		}
		PopulateComments(Offset, PluginId) //Populate comments in case of page refresh :)
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


function SaveDB() {
	Storage = GetStorage()
	//alert('Storage Offset='+window.Offset)
	//Storage[GetSeed()][window.Offset] = ToStr(Review[Offset])
	//Storage[GetSeed()] = ToStr(window.Review)
	Storage[GetSeed()] = ToStr(GetWorkReview())
	//alert(ToStr(Storage))
	
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

function HidePlugin(Offset, PluginId) {
	SetClassNameToElems(new Array('tab_'+ Offset + "_" +PluginId), 'tab_plugin')
	SetClassNameToElems(new Array( Offset + "_" +PluginId), 'tab-pane')
	return null
	//return false
}

function MarkIcon(ID, Init) {
	Elem = $("#" + ID)
	if (!Init) {
		IconRow = Elem.parent().parent() //Go up until the <tr> element so that we can unmark brothers and mark this one
		for (i = 0, length = IconRow.children().children().length; i < length; i++) {
			
			child = $(IconRow.children().children()[i])
			child.removeClass(child.data("hltype"))
			child.removeClass("active")
			
		}
	}
	
    
	Elem.addClass("active")  //Now mark as selected
	Elem.addClass(Elem.data("hltype"))
}

function Rate(Offset, PluginId, Rating, Elem) {
	MarkIcon(Elem.id, false)
	TabId = "tab_" + Offset + "_" +  PluginId
	
	if ('delete' == Rating) {
		Rating = 'N' //Keep the flag == 'N' for filter counter to work right
	}
	
	//console.log('Rate -> Logging Review[' + Offset + '] ..', Review[Offset])
	//console.log('Rate -> Logging Review[' + Offset + '][' + PluginId + '] ..', Review[Offset][PluginId])
	PreviousValue = Review[Offset][PluginId]['flag'] 
	//console.log('Rate -> Logging Review[' + Offset + '][' + PluginId + '][flag] ..', PreviousValue)
	NewValue = Review[Offset][PluginId]['flag'] = Rating 
	UpdatePluginCounter(Offset, PluginId, 'flag', PreviousValue, NewValue, $("#" + Elem.Id).hasClass("active"))
	SaveDB()
	ApplyReview(Offset) // Now update colours, etc
	//HidePlugin(Offset, PluginId)
}

function NotBooleanStr(BooleanStr) {
	if (BooleanStr == 'Y') {
		return 'N'
	}
	return 'Y'
}

function MarkAsSeen(Offset, PluginId) {
	PreviousValue = Review[Offset][PluginId].seen
	NewValue = Review[Offset][PluginId].seen = NotBooleanStr(PreviousValue)
	UpdatePluginCounter(Offset, PluginId, 'seen', PreviousValue, NewValue,false)
	SaveDB()
	ApplyReview(Offset)
	HidePlugin(Offset, PluginId)
}

function MarkAsFav(Offset, PluginId) {
	PreviousValue = Review[Offset][PluginId].fav
	NewValue = Review[Offset][PluginId].fav = NotBooleanStr(PreviousValue)
	UpdatePluginCounter(Offset, PluginId, 'fav', PreviousValue, NewValue,false)
	SaveDB()
	ApplyReview(Offset)
	//HidePlugin(Offset, PluginId)
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
	return PluginIds;
}

function GetPluginIdsWhereFieldMatches(Offset, Field, Value) {
	PluginIds = new Array()
	for (PluginId in Review[Offset]) {
		if (Review[Offset][PluginId][Field] == Value) {
			PluginIds.push(PluginId)
		}
	}
	return PluginIds
}

function GetSeenPlugins(Offset) {
	return GetPluginIdsWhereFieldMatches(Offset, 'seen', 'Y')
}

function ApplyReview(Offset) {
		SetStyleToPlugins(Offset, window.ReportsInfo[Offset].AllPlugins, '')
		SetStyleToPlugins(Offset, GetSeenPlugins(Offset), 'line-through')
		//ApplyCounters(window.ReportsInfo[Offset].AllPlugins, 'filter', true)
}

function HighlightNewPlugins(Offset) {//Looks for differences from the previous page load to current one, highlighting new plugins shown
	//This makes it easy to see what has happened since the last refresh
	//console.log('HighlightNewPlugins -> start', 'Review[' + Offset + ']', Review[Offset])
	//console.group('Plugin loop')
	for (i=0, length = window.ReportsInfo[Offset].AllPlugins.length; i<length; i++) {
		PluginId = window.ReportsInfo[Offset].AllPlugins[i]
		//console.log('Review[' + Offset + '][' + PluginId + ']')
		//console.log(Review[Offset][PluginId])
		if (Review[Offset][PluginId].new == 'Y') {
			Tab = GetById('tab_'+Offset+"_"+PluginId)
			//Link = GetById('l'+window.ReportsInfo[Offset].AllPlugins[i])
			if (Tab != null) {
				Tab.style.backgroundColor = '#000'//Highlighting with colours looks horrible, white background seems ok to me
				//Link.innerHTML = "->"+Link.innerHTML+"<-"
				//Tab.firstChild.innerHTML = Tab.firstChild.innerHTML+"*"
			}
		}
	}
}

function SetStyleToPlugins(Offset, PluginArray, StyleText) {
	//console.log('SetStyleToPlugins -> Review[' + Offset + ']=', Review[Offset])
	for (i=0, length = PluginArray.length; i<length; i++) {
		PluginId = PluginArray[i]
		StrikeIcon = GetById('l'+Offset+"_"+PluginId)
		TabId = 'tab_'+Offset+"_"+PluginId
		Tab = GetById(TabId)

		if (Tab != null) {
			Tab.style.textDecoration = StyleText
			//alert(Tab.name)
			//Tab.style.textDecoration = StyleText
			//console.log('SetStyleToPlugins -> Review[' + Offset + '][' + PluginId + ']=')
			//console.log(Review[Offset][PluginId])
			//console.log(Review[Offset][PluginId]['flag'])
			Flag = Review[Offset][PluginId]['flag']
			/*if (Flag == "fav") TabSpan = $("#" + TabId + " i:eq(0)")
			else if ($.inArray(Flag, SeverityFlags) != -1) TabSpan = $("#" + TabId + " i:eq(2)")
			else TabSpan = $("#" + TabId + " i:eq(1)")*/
			TabSpan = $("#" + TabId + " i:eq(0)")

			
			TabSpan.removeClass();
			TabSpan.toggleClass(FlagIcons[Flag])
			

			RatingId = Offset+"_"+PluginId + Flag
			if (Flag != 'N' && document.getElementById(RatingId) != null) {//Check valid flag exists
				MarkIcon(RatingId, true)
			}
			if ('' == StyleText) { //Not Seen
				//Link.firstChild.innerHTML = '<img src="images/pencil.png" title="Strike-through" />'
				StrikeIcon.innerHTML = '<i class="icon-eye-open"></i>'
			}
			else {
				//Link.firstChild.innerHTML = '<img src="images/eraser.png" title="Unstrike-through" />'
				StrikeIcon.innerHTML = '<i class="icon-eye-close"></i>'
			}
		}
	}
}

function ClearReview() {
	if (confirm("You are going to delete all the information for this review. Are you sure?")) {
		BlankReview()
		InitDB()
		//InitCounters(Prefix, '0')
		Refresh() //Normal page reload = to refresh summary + iframes
		
	}
}

function DeleteStorage() {
	if (confirm("You are going to delete all the information for ALL REVIEWS. Are you sure?")) {
		BlankReview()
		DestroyStorage()
		InitDB()
		//InitCounters(Prefix, '0')
		Refresh() //Normal page reload = to refresh summary + iframes

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
		//InitCounters(Prefix, '0')
		Refresh() //Normal page reload = to refresh summary + iframes
	}
}

function GetNotesDivId(Offset, PluginId) { return 'notes_'+Offset+'_'+PluginId }

function ToggleNotesBox(Offset, PluginId) {
	var DivId = GetNotesDivId(Offset,PluginId)
	DestroyEditors(Offset, PluginId) //Destroy all other instances to keep the report lightweight
	if (GetById(DivId).style.display == 'none') {
		var Editor = CreateEditor(Offset, PluginId)
	}
	SetEditorCommentsFromStorage(Offset, PluginId)
	ToggleDiv(DivId)
}

function GetStorageComments(Offset, PluginId) {
	return Review[Offset][GetRealPluginId(PluginId)].notes
}

function SetEditorCommentsFromStorage(Offset, PluginId) {
	var EditorId = GetEditorId(Offset, PluginId)
	Data = GetStorageComments(Offset, PluginId)
	//alert("EditorId = "+ EditorId +"\n" + Data )
	GetById(EditorId).value = Data
}

function PopulateComments(Offset, PluginId) {
	SetEditorCommentsFromStorage(Offset, PluginId)
	//$( '#' + EditorId ).val( Review[Offset][GetRealPluginId(PluginId)].notes );
	SetEditorPreview(Offset, PluginId, Data)
}

function GetEditorId(Offset, PluginId) { return 'note_text_'+ Offset+ '_' + PluginId }
function GetEditor(Offset, PluginId) { 
	var EditorId = GetEditorId(Offset, PluginId)
	try { //Try to get existing editor first
		var Editor = $('#' + EditorId).ckeditorGet() 
	}
	catch (e) { //Editor doesn't exist, create it and return it
		var Editor = $( '#' + EditorId).ckeditor().ckeditorGet()
	}
	return Editor
}

function SetEditorPreview(Offset, PluginId, Data) { 
	var Ids = [ Offset+ "_" +PluginId ]
	if (IsReportPluginId(PluginId)) {
		Ids.push ( Offset + "_" + GetRealPluginId(PluginId) )
	}
	for (var i in Ids) {
		Id = Ids[i]
		GetById('note_preview_' + Id).innerHTML = Data.replace(/<a href/g, '<a target="_blank" href') //Open links in new tab, cumbersome otherwise ..
	}
}

function DestroyEditors(ToggledOffset, ToggledPluginId) { //Destroy all Editors to save resources
	for (var Id in CKEDITOR.instances) {
		CKEDITOR.instances[Id].destroy()
		AffectedPluginId = Id.replace('note_text_', '')
		if (AffectedPluginId != ToggledOffset+'_'+ ToggledPluginId) { //Only hide other editors' divs, not the current one
			ToggleDiv(GetNotesDivId(ToggledOffset, AffectedPluginId)) //Hide affected plugin div so that things look normal
		}
	}
	//delete CKEDITOR.instances.cause
}

function CreateEditor(Offset, PluginId) { //Listen on the right events to save pen tester input as it is typed
	//Somewhat helpful links:
	//http://alfonsoml.blogspot.com/2011/03/onchange-event-for-ckeditor.html
	//http://stackoverflow.com/questions/5879832/how-to-listen-for-ckeditor-event-setdata-with-jquery
	var Editor = GetEditor(Offset, PluginId)
	//Must listen to a number of events due to lack of proper "onchange" event (somewhat surprising given the awesomeness of this editor)
	Editor.on( 'key', function() { this.fire('change') });
	Editor.on( 'paste', function() { this.fire('change') });
	Editor.on( 'currentInstance', function() { this.fire('change') });
	Editor.on( 'selectionChange', function() { this.fire('change') });
	Editor.on( 'contentDom', function() { this.fire('change') });
	Editor.on( 'blur', function() { this.fire('change') });
	Editor.on( 'change', function() { SaveComments(Offset, PluginId) });
	Editor.on( 'instanceReady', function() { this.fire('load') });
	Editor.on( 'load', function() { SetEditorCommentsFromStorage(Offset, PluginId) });
	return Editor
}

function SaveComments(Offset, PluginId) {
	//Review[Offset][GetRealPluginId(PluginId)].notes = GetById('note_text_'+PluginId).value
	//Review[Offset][GetRealPluginId(PluginId)].notes = CKEDITOR.instances['note_text_'+PluginId].getData();
	//Review[Offset][GetRealPluginId(PluginId)].notes = $( '#' + EditorId ).val();
	//Review[Offset][GetRealPluginId(PluginId)].notes = $( '#' + EditorId ).ckeditorGet().getData()
	var Data = GetEditor(Offset, PluginId).getData()
	if (Data == Review[Offset][GetRealPluginId(PluginId)].notes) { //No changes = nothing to do!
		return false
	}
        var CommentsBefore = PluginCommentsPresent(Offset, PluginId) //Comments here before = increment happened before too
	Review[Offset][GetRealPluginId(PluginId)].notes = Data
	SetEditorPreview(Offset, PluginId, Data)
        var CommentsNow = PluginCommentsPresent(Offset, PluginId)
	var CommentsCounter = GetCounterFromField('notes')
	if (!CommentsBefore && CommentsNow) { UpdateCounter(Offset,  CommentsCounter, +1 ) }
	if (CommentsBefore && !CommentsNow) { UpdateCounter(Offset, CommentsCounter, -1 ) } //Decrement = one plugin less with notes
	SaveDB()
}

function SetDisplayToAllPluginTabs(Display) {
		for (var Offset in window.ReportsInfo ) {
	        for (var i=0, length = window.ReportsInfo[Offset].AllPlugins.length; i<length; i++) {
                var PluginId = window.ReportsInfo[Offset].AllPlugins[i]

		GetById('tab_'+Offset+"_"+PluginId).style.display = Display
		GetById('tab_'+Offset+"_"+PluginId).className = ''
	        }
		}
}

function SetDisplayToAllPluginTabsByOffset(Offset, Display) {
        for (var i=0, length = window.ReportsInfo[Offset].AllPlugins.length; i<length; i++) {
            var PluginId = window.ReportsInfo[Offset].AllPlugins[i]
	GetById('tab_'+Offset+"_"+PluginId).style.display = Display
	GetById('tab_'+Offset+"_"+PluginId).className = ''
        }
	}


function SetDisplayToAllTestGroups(Display) {
	AccordionGroups = document.getElementsByClassName('accordion-group')
	for (i = 0; i < AccordionGroups.length; i++) {
		AccordionGroups[i].style.display = Display
	}
}

function SetDisplayToAllTestGroupsByOffset(Offset, Display) {
	AccordionGroups = $('#section_' + Offset + ' .accordion-group')
	if (Display=="none") AccordionGroups.hide()
	else AccordionGroups.show()
}

function PluginCommentsPresent(Offset, PluginId) {
	return (Review[Offset][GetRealPluginId(PluginId)].notes.length > 0)
}


function SelfGetDetailedReport(Offset) { //Gets the iframe from parent window
	return document.getElementById('section_' + Offset) //Retrieve self from parent
}

function DetailedReportCollapse(Offset) {
	Section = SelfGetDetailedReport(Offset)
	// Collapse all testgroups here
}

function DetailedReportAdjust(Offset) {
	Section = SelfGetDetailedReport(Offset)
	// no need
}

function DetailedReportExpand(Offset) {
	Section = SelfGetDetailedReport(Offset)
	// Expand all test-groups here
}

function DetailedReportAnalyse(Offset) {
	DetailedReportExpand(Offset)
	//window.parent.location.hash = 'anchor_' + Offset
}

function SelfAutoResize(Offset) {
	DetailedReportCollapse(Offset)
	DetailedReportAdjust(Offset)
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
