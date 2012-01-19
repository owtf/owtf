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
	InitDB()
	if (IsDetailedReport()) {
		ApplyReview() //Apply reviewed plugins
		HighlightNewPlugins() //Right after loading, only once, highlight the new plugins
		ClickLinkById('tab_filter') //Enable Filter tab by default
		ClickLinkById('filterinfo') //Click on Filter by information only
	}
	else { //Assuming Summary report:
		RefreshCounters()
		ClickLinkById('tab_filter') //Enable Filter tab by default
	}
}
); 

function IsDetailedReport() {
	return window.DetailedReport
}

function ToStr(Variable) {
	return JSON.stringify(Variable)
}

function FromStr(Variable) {
	if (Variable == null) {
		return {}
	}
	try {
		return JSON.parse(Variable)
	}
	catch(e) {//Garbage passed, i.e. when deleting DB Variable is an object and this blows
		//alert('Variable='+Variable)
		return {}
	}
}

function GetSeed() {
	return GetById('seed').innerHTML
}

function GetPluginToken(PluginId) {
	return GetById('token_'+PluginId).innerHTML
}

function InitDB() {//Ensure all completed plugins have a review offset
	window.Review = GetDB()
	if (Review == null) {
		Review = {} //The review is a JSON object, which is converted into a string for storage after updating
	}
	if (IsDetailedReport()) {
		InitDetailedReport()
	}
}

function InitDetailedReport() {
	//alert("Offet="+Offset)
	if (Review[Offset] == null) {
		Review[Offset] = {}
	}
	for (i=0, length = window.AllPlugins.length; i<length; i++) {
		PluginId = window.AllPlugins[i]
		PluginToken = GetPluginToken(PluginId)
		if (Review[Offset][PluginId] == null) { //Review not initialised for plugin
			Review[Offset][PluginId] = { 'seen' : 'N', 'flag' : 'N', 'new' : 'Y', 'notes' : '', 'tk' : GetPluginToken(PluginId) }
		}
		else if (PluginToken != Review[Offset][PluginId].tk) {//Plugin changed (i.e. forced overwrite or grep plugin, highlight change)
			Review[Offset][PluginId].new = 'Y'
			Review[Offset][PluginId].tk = PluginToken //keep token to detect future changes
		}
		else { //Plugin has not changed, flag as not new:
			Review[Offset][PluginId].new = 'N'
		}
		PopulateComments(PluginId) //Populate comments in case of page refresh :)
	}
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
	GetById('js_db_size').innerHTML = GetDBUsedMemory()+' KB' //Update DB Size on screen
	GetById('total_js_db_size').innerHTML = GetStorageUsedMemory()+' KB'
}

function SaveDB() {
	Storage = GetStorage()
	//alert('Storage Offset='+window.Offset)
	//Storage[GetSeed()][window.Offset] = ToStr(Review[Offset])
	Storage[GetSeed()] = ToStr(window.Review)
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

function GetById(Id) { //jQuery wrapper to make it easier to find bugs
        //Elem = $("#"+Id);
        Elem = document.getElementById(Id)
	if (Elem == null) {
		alert('BUG: Id='+Id+' is null')
	}
	return Elem
}

function ToggleDivElem(Div) {
        Div.style.display = ((Div.style.display == 'block') ? 'none' : 'block'); 
        return false; 
}

function ToggleDiv(divid) {//Hides or Shows the passed div depending on whether it is currently being shown or not 
        return ToggleDivElem(GetById(divid));
}

function ToggleDivs(DivArray) {//Toggles a bunch of divs
        for (var i=0, len=DivArray.length; i<len; ++i) {
                ToggleDivElem(GetById(DivArray[i]));
        }
        return false;
}

function SetDisplayToDivs(DivArray, Display) {//Modifies the display of all passed divs to whatever was passed on "Display"
        for (var i=0, len=DivArray.length; i<len; ++i) {
                d = GetById(DivArray[i]);
                d.style.display = Display;
        }
        return false;
}
function ShowDivs(DivArray) {//Set a bunch of divs to be shown
        return SetDisplayToDivs(DivArray, 'block');
}

function HideDivs(DivArray) {//Set a bunch of divs to be hidden
        return SetDisplayToDivs(DivArray, 'none');
}

function HidePlugin(PluginId) {
	HideDivs(new Array(PluginId))
	return SetClassNameToElems(new Array('tab_'+PluginId), '')
	//return false
}

function OpenAllInTabs(LinkArray) {//In Firefox at least, the code here will open a new tab per link contained in the passed array
        for ( var i=0, len=LinkArray.length; i<len; ++i) {
                window.open(LinkArray[i])
        }
        return false
}

function SetClassNameToElems(ElemArray, ClassNameValue) {
        for (var i=0, len=ElemArray.length; i<len; ++i) {
                Elem = GetById(ElemArray[i])
                Elem.className = ClassNameValue
        }
        return false
}

function ClickLinkById(LinkId) {
    ClickLink(GetById(LinkId))
}

//Below is largely courtesy of: http://stackoverflow.com/questions/902713/how-do-i-automatically-click-a-link-with-javascript
function ClickLink(Link) {
	var Cancelled = false;

	if (document.createEvent) {
		var event = document.createEvent("MouseEvents");
		event.initMouseEvent("click", true, true, window,
		0, 0, 0, 0, 0,
		false, false, false, false,
		0, null);
		Cancelled = !Link.dispatchEvent(event);
	}
	else if (Link.fireEvent) {
		Cancelled = !Link.fireEvent("onclick");
	}

	if (!Cancelled) {
		window.location = Link.href;
	}
}

function Rate(PluginId, Rating) {
	if ('delete' == Rating) {
		Rating = 'N' //Keep the flag == 'N' for filter counter to work right
	}
	Review[Offset][PluginId]['flag'] = Rating
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
	Review[Offset][PluginId].seen = NotBooleanStr(Review[Offset][PluginId].seen)
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
	SetStyleToPlugins(window.AllPlugins, '')
	SetStyleToPlugins(GetSeenPlugins(), 'line-through')
	ApplyCounters(window.AllPlugins, 'filter', true)
}

function HighlightNewPlugins() {//Looks for differences from the previous page load to current one, highlighting new plugins shown
	//This makes it easy to see what has happened since the last refresh
	for (i=0, length = window.AllPlugins.length; i<length; i++) {
		PluginId = window.AllPlugins[i]
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
	for (i=0, length = PluginArray.length; i<length; i++) {
		PluginId = PluginArray[i]
		Heading = GetById('h'+PluginId)
		StrikeIcon = GetById('l'+PluginId)
		Tab = GetById('tab_'+PluginId)
		if (Tab != null) {
			Tab.style.textDecoration = Heading.style.textDecoration = StyleText
			//alert(Tab.name)
			//Tab.style.textDecoration = StyleText
			Tab.parentNode.className = Review[Offset][PluginId]['flag']
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

function RefreshReport() { //Normal page reload
	window.location.reload()
}

function ShowUsedMem() {
	alert('Memory in use by review storage: '+GetStorageUsedMemory()+' KB')
}

function ShowUsedMemPercentage() {
	alert('Memory in use by review storage: '+GetStorageMemoryPercent()+' %')
}

function ExportReviewAsText() {
	GetById('import_export_box').value = ToStr(window.Review)
	//GetById('import_export_box').value = GetStorage()[GetSeed()]
        //localStorage["AllPlugins"+Seed] //localStorage won't work in FF over file://
        //sessvars["AllPlugins"+Seed]
}

function ExportReviewAsFile() {//not working yet
	save_content_to_file('owtf_review_export.txt', ToStr(window.Review))
}

function ImportReview() {
	if (confirm('This action may erase THIS review data. Are you sure?')) {
		window.Review = FromStr(GetById('import_export_box').value)
		SaveDB()
		InitDB()
		ApplyReview()
	}
}

function ToggleNotesBox(PluginId) {
	return ToggleDiv('notes_'+PluginId)
}

function PopulateComments(PluginId) {
	GetById('note_text_'+PluginId).value =  Review[Offset][PluginId].notes
}

function SaveComments(PluginId) {
	Review[Offset][PluginId].notes = GetById('note_text_'+PluginId).value
        if (PluginCommentsPresent(PluginId)) {
        	IncrementCounter('filter', 'notes_counter') //Increment notes counter
        }
	SaveDB()
}

function SetDisplayToAllPluginTabs(Display) {
        for (i=0, length = window.AllPlugins.length; i<length; i++) {
                PluginId = window.AllPlugins[i]
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

function UnFilterPlugin(PluginId) {
	//GetById('tab_'+PluginId).style.display = 'block' //Show the tab
	GetById(PluginId).parentNode.style.display = 'block' //Show the test group 
	GetById('tab_'+PluginId).parentNode.style.display = ''//Show the tab
}

function UnFilterPlugins(PluginArray) {
	for (i = 0; i < PluginIds.length; i++) {
		PluginId = PluginIds[i]
		UnFilterPlugin(PluginId)
	}
}

function UnFilterPluginsWhereFieldMatches(Field, Value) {
	UnFilterPlugins(GetPluginIdsWhereFieldMatches(Field, Value))
}

function PluginCommentsPresent(PluginId) {
	return (Review[Offset][PluginId].notes.length > 0)
}

function UnfilterPluginsWhereCommentsPresent() {
	for (i = 0; i < window.AllPlugins.length; i++) {
		PluginId = window.AllPlugins[i]
		if (PluginCommentsPresent(PluginId)) {
			UnFilterPlugin(PluginId)
		}
	}
}

function SetDisplayUnfilterPlugins(Display) {
	UnfilterPluginIcons = document.getElementsByClassName('icon_unfilter')
	for (i = 2, length = UnfilterPluginIcons.length; i < length; i++) { //NOTE: Start with i = 2 to skip the first icons on the top tabs
		IconLink = UnfilterPluginIcons[i]
		IconLink.style.display = Display
	}
}

function IncrementInnerHTML(Id) {
	GetById(Id).innerHTML = parseInt(GetById(Id).innerHTML) + 1
}

function IncrementCounter(Prefix, CounterId) {
	IncrementInnerHTML(Prefix+CounterId)
	if (!DetailedReport) { //Also increment totals in summary report
		IncrementInnerHTML('filter'+CounterId)
	}
}

function FilterResults(Parameter) {
	if ('refresh' == Parameter) {//Only refresh the page
		RefreshReport() //Normal page reload
		return false
	}
	//Step 1 - Hide everything
	//SetDisplayToAllPluginTabs('none') //Hide all plugin tabs
	SetDisplayToDivs(window.AllPlugins, 'none')//Hide all plugin divs
	SetDisplayToAllTestGroups('none') //Hide all index divs
	SetDisplayToAllPluginTabs('none') //Hide all plugin tabs (it's confusing when you filter and see flags you did not filter by)
	SetDisplayUnfilterPlugins('')
	HighlightFilters('')
	//Step 2 - Apply filter: Show whatever is relevant
	if ('seen' == Parameter) {
		UnFilterPluginsWhereFieldMatches('seen', 'Y')
	}
	else if ('unseen' == Parameter) {
		UnFilterPluginsWhereFieldMatches('seen', 'N')
	}
	else if ('notes' == Parameter) {
		UnfilterPluginsWhereCommentsPresent()
	}
	else if ('delete' == Parameter) {//Remove filter
		//SetDisplayToAllPluginTabs('block')//Show all plugin tabs
		SetDisplayToAllTestGroups('block')//Show all index divs
		SetDisplayToAllPluginTabs('') //Show all plugin tabs again (display = block looks horrible :))
		SetDisplayUnfilterPlugins('none') //Undo filter for brother plugins button hidden
	}
	else if ('info' == Parameter) {//Show with info
		UnFilterPluginsWhereFieldMatches('seen', 'Y')
		UnFilterPluginsWhereFieldMatches('seen', 'N')
		SetDisplayUnfilterPlugins('none') //Undo filter for brother plugins button hidden
	}
	else if ('no_flag' == Parameter) {//Show without flags
		UnFilterPluginsWhereFieldMatches('flag', 'N')
	}
	else {
		UnFilterPluginsWhereFieldMatches('flag', Parameter)
	}
	HighlightFilter('filter'+Parameter, 'active')
}

function BlankNonCounters() {
	GetById('filterrefresh_counter').innerHTML = GetById('filterdelete_counter').innerHTML = ''
}

function HighlightFilter(FilterId, Highlight) {
	GetById(FilterId).parentNode.className = Highlight
}

function HighlightFilters(Highlight) {
	for (i=0, length = window.AllCounters.length; i<length; i++) { 
		CounterId = window.AllCounters[i]
		FilterId = CounterId.replace('_counter', '')
		HighlightFilter(FilterId, Highlight)
	}
}

function SetCounterColour(CounterId, Prefix) {
	PluginFlag = CounterId.replace(Prefix, '').replace('_counter', '')
	//alert('PluginFlag='+PluginFlag)
	SetColourFromFlag(CounterId, PluginFlag)
}

function InitCounters(Prefix, Amount) {
	for (i=0, length = window.AllCounters.length; i<length; i++) {
		CounterId = window.AllCounters[i]
		if (Amount == '0') { GetById(CounterId).innerHTML = Amount }
		SetCounterColour(CounterId, Prefix)
	}
	BlankNonCounters()
}

function ApplyCounters(PluginArray, Prefix, Init) {
	if (Init) {
		InitCounters(Prefix, '0')
	}
	for (i=0, length = PluginArray.length; i<length; i++) {
		PluginId = PluginArray[i]
		IncrementCounter(Prefix, 'info_counter')
		if (Review[Offset][PluginId].seen == 'Y') {
			IncrementCounter(Prefix, 'seen_counter') //Increment striken-through
		}
		else { //not seen
			IncrementCounter(Prefix, 'unseen_counter') //Increment unstriken-through
		}
		PluginFlag = Review[Offset][PluginId].flag
		if (PluginFlag == 'N') {
			IncrementCounter(Prefix, 'no_flag_counter') //Increment unstriken-through
		}
		else { //Increase relevant flag
			CounterId = PluginFlag+'_counter'
			IncrementCounter(Prefix, CounterId)
		}
		if (PluginCommentsPresent(PluginId)) {
			IncrementCounter(Prefix, 'notes_counter') //Increment notes counter
		}
	}
	BlankNonCounters()
}

function MultiIncrement(CounterArray) {
	for (Offset in CounterArray) {
		for (Counter in CounterArray[Offset]) {
			for (i=0, length = CounterArray[Offset][Counter]; i<length; i++) {
				IncrementCounter(Offset, Counter)
			}
		}
	}
}

function RefreshCounters() {
	UpdateMemoryCounters()
	CounterArray = {}
	for (Offset in PluginCounters) {
		//alert('Processing Offset='+Offset)
		PluginsFinished = parseInt(PluginCounters[Offset])
		InitCounters(Offset) //1st count what was reviewed
		if (Review[Offset] == null || Review[Offset] == {}) {
			CounterArray[Offset] = { 'info_counter' : PluginsFinished, 'no_flag_counter' : PluginsFinished, 'unseen_counter' : PluginsFinished }
		}
		else {
			//alert(GetPluginIdsForOffset(Offset))
			ApplyCounters(GetPluginIdsForOffset(Offset), Offset, false) //1st count what was reviewed
			//2nd - calculate increments for what was not reviewed:
			CounterArray[Offset] = {} //Fondle JavaScript ;)
			CounterArray[Offset]['no_flag_counter'] = PluginsFinished - parseInt(GetById(Offset+'info_counter').innerHTML)
			CounterArray[Offset]['info_counter'] = PluginsFinished - parseInt(GetById(Offset+'info_counter').innerHTML)
			CounterArray[Offset]['unseen_counter'] = PluginsFinished - parseInt(GetById(Offset+'unseen_counter').innerHTML) - parseInt(GetById(Offset+'seen_counter').innerHTML)
		}
	}
	MultiIncrement(CounterArray)
}

function SetColourFromFlag(CounterId, PluginFlag) {
	Colour = PluginFlag.split('_')[1]
	if (jQuery.inArray(Colour, [ 'green', 'blue', 'yellow', 'orange', 'red', 'violet' ]) != -1) {//Colour is valid
		GetById(CounterId).style.color = GetColourFromWord(Colour)
	}
}

function GetColourFromWord(Word) {
	if (Word == 'yellow') { //Chosee darker tones so that number can be seen :)
		Word = '#C0C000' 
	}
	else if (Word == 'orange') {
		Word = '#FF8C0D' 
	}
	return Word
}

function UnfilterBrotherTabs(Link) {
	UL = Link.parentNode.parentNode //Go up until the <ul> element so that we can remove the style filter on the <li> elements
	for (i = 0, length = UL.childNodes.length; i < length; i++) {
		if (UL.childNodes[i].style) {
			UL.childNodes[i].style.display = ''
		}
	}
}

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
