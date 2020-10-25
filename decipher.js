function decrypt_page () {
    var key_str = "";
    var html_name = window.location.href.split("/").slice(-1)[0].split(".")[0];
    var allcookies = document.cookie;
    cookiearray = allcookies.split(';');
    for(var i=0; i<cookiearray.length; i++) {
        name = cookiearray[i].split('=')[0].trim();
        value = cookiearray[i].split('=')[1];
        if (name == html_name)
            key_str = value;
	if (name == "__master__") {
	    key_str = value;
	    break;
	}
	    
    }
    while (true) {
	// check key length
        if (key_str.length != 16 &&
	    key_str.length != 24 &&
	    key_str.length != 32)
	{
            console.log("wrong length:" + key_str.length)
            var key_str = prompt("Please enter the key. \nThe key will be stored as a cookie so you will not have to enter it again", "");
            if (!key_str) {
		window.location.href = "index.html";
		return;
	    }
	    continue;
        }
        var entered_key = aesjs.utils.utf8.toBytes(key_str);
        var enc_bytes = aesjs.utils.hex.toBytes(enc_hex_body)

	// check if the user input / loaded cookie is the master key
        var aesCtr = new aesjs.ModeOfOperation.ctr(entered_key, new aesjs.Counter())
        var master_key_dec_real_key = aesCtr.decrypt(aesjs.utils.hex.toBytes(master_key_enc_real_key))

	aesCtr = new aesjs.ModeOfOperation.ctr(master_key_dec_real_key, new aesjs.Counter())
	var dec_bytes = aesCtr.decrypt(enc_bytes)

        // Convert our bytes back into text
        var dec_text = aesjs.utils.utf8.fromBytes(dec_bytes)
        if (!dec_text.startsWith(correct_key_marker)) {
            // check if it is a regular password
	    aesCtr = new aesjs.ModeOfOperation.ctr(entered_key, new aesjs.Counter())
            var org_key_dec_real_key = aesCtr.decrypt(aesjs.utils.hex.toBytes(org_key_enc_real_key))

	    aesCtr = new aesjs.ModeOfOperation.ctr(org_key_dec_real_key, new aesjs.Counter())
	    dec_bytes = aesCtr.decrypt(enc_bytes)
	    dec_text  = aesjs.utils.utf8.fromBytes(dec_bytes)
            
	    if (!dec_text.startsWith(correct_key_marker)) {
		key_str = "";
		continue;
	    } else {
		// entered correct file key
		document.cookie = html_name + "=" + key_str;
	    }
        } else {
	    // entered correct master key
	    document.cookie = "__master__=" + key_str;
	}
	
	// Convert our bytes back into text
        var dec_text = aesjs.utils.utf8.fromBytes(dec_bytes)
        document.body.innerHTML = dec_text

        $('.bs-docs-sidebar li').first().addClass('active');
        $(document.body).scrollspy({target: '.bs-docs-sidebar'});
        $('.bs-docs-sidebar').affix();
        break;
    }
}

window.onload = decrypt_page
