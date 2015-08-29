/*
Database abstraction functions to use localStorage under the hood
*/
function DestroyStorage() {
	for (key in localStorage) {
		localStorage[key] = {}
	}
	localStorage = {}
        delete localStorage
}

function GetStorage() {//To make it easy to change to other stuff in the future or maybe make this configurable
        return localStorage //localStorage does not work in Firefox for file:// URLs
}

function GetStorageSize() {
	return 5000
}
