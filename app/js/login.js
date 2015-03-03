require.config({
    paths: {
        'jquery': '/js/vendor/jquery',
        'domReady': '/js/vendor/domReady',
    }
});

require(['jquery', 'domReady!'],
function (jquery)
{
    var fields = [ "username", "password" ];
    var errmode = false;

    function validate() {
        var data = {}
        for (var i = 0; i < fields.length; i++) {
            var value = jquery.trim(jquery('#'+fields[i]).val());
            if (value.length == 0) {
                return false;
            }
            data[fields[i]] = value;
        }
        return data;
    }

    function change(node) {
        if (node.val().length == 0) {
            node.addClass('error');
        } else {
            node.removeClass('error');
        }
    }

    function getParam(name)
    {
        var qs = window.location.search.substring(1);
        var tokens = qs.split('&');
        for (var i = 0; i < tokens.length; i++) 
        {
            var param = tokens[i].split('=');
            if (param[0] == name)
            {
                return param[1];
            }
        }
        return null;
    }

    function submit() {
        var data = validate();
        if (!data) {
            return setErrorMode();
        }
        var redirect = getParam("location");
        if (redirect != null) {
            jquery('#redirect').val(redirect);
        }
        jquery('form').submit();
    }

    function setErrorMode() {
        if (errmode) {
            return;
        }
        for (var i = 0; i < fields.length; i++) {
            var node = jquery('#'+fields[i]); // must re-grab the node
            node.keyup(function(event) {
                change(node);
            });
            change(node);
        }
        errmode = true;

        jquery('#error').removeClass('hidden');
    }

    if (jquery('#auth-error').length) {
        setErrorMode();
        jquery('#error').removeClass('hidden');
    }

    jquery('#login').bind('click', function(event) {
        event.preventDefault();
        submit();
    });
});
