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
