function change_skin(skin_id,skin_type) {
	
   $("#skin_css").attr("href", "includes/css/skins/" + skin_id +".css" );
   

   logo_type ="dark"; // dark is the default logo type
   if (skin_type == "dark") { logo_type="light"; }  // RTL is not ready for skins
	
   $('img[alt="OWASP_OWTF_LOGO"]').attr("src", "includes/img/logo_"+logo_type+".png" );

   setSkinCookie(skin_id+"_"+skin_type)
}

function setSkinCookie(skin_id)
{

	var exdays = 300; // expiration time
	var c_name = "skin"; // cookie_name
	var exdate=new Date();
	exdate.setDate(exdate.getDate() + exdays);
var c_value=escape(skin_id) + ((exdays==null) ? "" : ";path=/; expires="+exdate.toUTCString());
document.cookie=c_name + "=" + c_value;
}

function GetSkinCookieAndApply() 
{
	var c_name = "skin"; // cookie_name
	var c_value = document.cookie;
	var c_start = c_value.indexOf(" " + c_name + "=");
	if (c_start == -1)
	  {
	  c_start = c_value.indexOf(c_name + "=");
	  }
	if (c_start == -1)
	  {
	  c_value = null;
	  }
	else
	  {
	  c_start = c_value.indexOf("=", c_start) + 1;
	  var c_end = c_value.indexOf(";", c_start);
	  if (c_end == -1)
	  {
	c_end = c_value.length;
	}
	c_value = unescape(c_value.substring(c_start,c_end));
	}
	
	//var skin_id = c_value;
	var st = c_value.split("_");
	var skin_id = st[0];
	var type = st[1];
	
	if (skin_id != null &&   skin_id != "null" && skin_id != "cyborg") change_skin(skin_id,type);
	
	
}
