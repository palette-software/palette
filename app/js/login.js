require.config({
    paths: {
        'jquery': '/js/vendor/jquery'
    }
});

require(['jquery'],
function ($)
{
    var fields = [ "username", "password" ];

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
        var input = $('#password');
        input[0].selectionStart = 0;
        input[0].selectionEnd = input.val().length;
        $('#error').removeClass('hidden');
    }

    $().ready(function () {
        var url = $('form').attr('action');
        $('#login').bind('click', function(event) {
            event.preventDefault();
            submit(url);
        });
    });
});
