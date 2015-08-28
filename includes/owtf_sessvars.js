/*
Database abstraction functions to use sessvars under the hood
*/
function DestroyStorage() {
        sessvars.$.clearMem() //Destroy everything
}

function GetStorage() {
        return sessvars
}

function _GetStorageUsedMemory() {
        return sessvars.$.usedMem()
}

function _GetStorageMemoryPercent() {
        return sessvars.$.usedMemPercent()
}

function GetStorageSize() {
        return 2000 
}

function ShowDebugWindow() {
        sessvars.$.debug()
        GetById('sessvarsDebugDiv').style.display = "block";
}

function HideDebugWindow() {
        GetById('sessvarsDebugDiv').style.display = "none";
}
