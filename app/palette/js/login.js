require.config({
    paths: {
        'jquery': '/app/module/palette/js/vendor/jquery',
        'domReady': '/app/module/palette/js/vendor/domReady',
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

    function submit() {
        var data = validate();
        if (!data) {
            return setErrorMode();
        }
        jquery('form').submit();
    }

    function setErrorMode() {
        if (errmode) {
            return;
        }
        for (var i = 0; i < fields.length; i++) {
            var node = jquery('#'+fields[i]);
            var val = node.parent().html();
            val += "<label for=\"" + fields[i] + "\" class=\"error\">" + 
                "This field is required.</label>";
            node.parent().html(val);

            var node = jquery('#'+fields[i]); // must re-grab the node
            node.keyup(function(event) {
                change(node);
            });
            change(node);
        }
        errmode = true;
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
