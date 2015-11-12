define(['jquery'],
function ($)
{
    /*
     * setCookie()
     */
    function setCookie(cname, cvalue, exdays) {
        var value = cname + "=" + cvalue.replace(/ /g, "_");
        if (exdays != undefined) {
            var d = new Date();
            d.setTime(d.getTime() + (exdays*24*60*60*1000));
            value += "; expires="+d.toUTCString();
        }
        value += "; path=" + "/";
        document.cookie = value;
    }

    /*
     * deleteCookie()
     * Delete a cookie by name by setting it to expire.
     */
    function deleteCookie(name) {
        document.cookie = name + '=;expires=Thu, 01 Jan 1970 00:00:01 GMT;';
    }

    /*
     * getCookie()
     */
    function getCookie(cname) {
        var name = cname + "=";
        var ca = document.cookie.split(';');
        for(var i=0; i < ca.length; i++) {
            var c = ca[i];
            while (c.charAt(0)==' ') {
                c = c.substring(1);
            }
            if (c.indexOf(name) != -1) {
                return c.substring(name.length, c.length).toString();
            }
        }
        return null;
    }

    $.fn.cookie = function(cname, cvalue, exdays) {
        if (cvalue == null) {
            return get(cname);
        } else {
            set(cname, cvalue, exdata);
        }
    };

    return {
        "set": setCookie,
        "get": getCookie,
        "remove": deleteCookie
    }
});
