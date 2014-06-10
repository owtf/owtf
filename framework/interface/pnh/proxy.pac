function FindProxyForURL(url,host) { 
	 if (host == "127.0.0.1") { 
	    return "DIRECT"; 
	 }
	 return "PROXY {{ proxy_details }}"; 
}
