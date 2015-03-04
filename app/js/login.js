require.config({
    paths: {
        'jquery': '/js/vendor/jquery',
        'domReady': '/js/vendor/domReady',
    }
});

require(['jquery', 'domReady!'],
function ($)
{
    var fields = [ "username", "password" ];
    var errmode = false;

    function validate() {
        var data = {}
        for (var i = 0; i < fields.length; i++) {
            var value = $.trim($('#'+fields[i]).val());
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

    function submit(url) {
        var data = validate();
        if (!data) {
            return setErrorMode();
        }
        var location = getParam("location");
        if (location == null) {
            location = '/';
        }
        $.ajax({
            type: "POST",
            url: url,
            data: $('form').serialize(),
            success: function () {
                window.location.replace(location);
            },
            error: function () {
                setErrorMode();
                $('#error').removeClass('hidden');
            }
        });
    }

    function setErrorMode() {
        if (errmode) {
            return;
        }
        for (var i = 0; i < fields.length; i++) {
            var node = $('#'+fields[i]); // must re-grab the node
            node.keyup(function(event) {
                change(node);
            });
            change(node);
        }
        errmode = true;

        $('#error').removeClass('hidden');
    }

    var url = $('form').attr('action');
    $('#login').bind('click', function(event) {
        event.preventDefault();
        submit(url);
    });
});
