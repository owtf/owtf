/*!
 * owtf JavaScript Library 
 * http://owtf.org/
 */

/*
	This file contains general-purpose functions
*/

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

function InArray(Needle, Stack) {
        return (jQuery.inArray(Needle, Stack) != -1)
}

function GetById(Id) { //jQuery wrapper to make it easier to find bugs
        //Elem = $("#"+Id);
        Elem = document.getElementById(Id)
        if (Elem == null) {
                // alert('BUG: Id='+Id+' is null')
        }
        return Elem
}

function ToggleDivElem(Div) {
        Div.style.display = ((Div.style.display == 'block' || Div.style.display == '') ? 'none' : 'block');
}

function ToggleDiv(divid) {//Hides or Shows the passed div depending on whether it is currently being shown or not 
        return ToggleDivElem(GetById(divid));
}

function ToggleDivs(DivArray) {//Toggles a bunch of divs
        for (var i=0, len=DivArray.length; i<len; ++i) {
                ToggleDivElem(GetById(DivArray[i]));
        }
}

function SetDisplayToDivs(DivArray, Display) {//Modifies the display of all passed divs to whatever was passed on "Display"
        for (var i=0, len=DivArray.length; i<len; ++i) {
                d = GetById(DivArray[i]);
                d.style.display = Display;
        }
}

function SetDisplayToDivsByOffset(Offset, DivArray, Display) {//Modifies the display of all passed divs to whatever was passed on "Display"
    for (var i=0, len=DivArray.length; i<len; ++i) {
            d = GetById(Offset+"_"+DivArray[i]);
            if (Display == "none") d.className = "tab-pane";
    }
}

function ShowDivs(DivArray) {//Set a bunch of divs to be shown
        return SetDisplayToDivs(DivArray, 'block');
}

function HideDivs(DivArray) {//Set a bunch of divs to be hidden
        return SetDisplayToDivs(DivArray, 'none');
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

function Refresh() { //Normal page reload // should be rewritten to reload only what we want to be reloaded
        window.location.reload()
		
}
