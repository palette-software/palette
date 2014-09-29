require(['jquery', 'topic', 'template', 'common', 'EditBox', 'OnOff', 'bootstrap'],
function ($, topic, template, common, EditBox, OnOff)
{
    var LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ";

    var active = false;
    var refresh_unavailable_text = 'Refresh not currently possible.';

    var startswith = null;

    function ddCallback(node, value) {
        var $section = $(node).closest('article');
        var old = $('.display-role', $section).html();
        if (/Publisher/i.test(old)) {
            if (value.toLowerCase() == 'none') {
                value = 'Publisher';
            } else {
                value = 'Publisher & ' + value;
            }
        }
        $('.display-role', $section).html(value);
    }

    function update(data) {
        $().ready(function() {
            var t = $('#user-list-template').html();
            var rendered = template.render(t, data);
            $('#user-list').html(rendered);
            $('div.dropdown').each(function () {
                $(this).data('callback', ddCallback);
            });
            common.bindEvents();
            common.setupDropdowns();
            EditBox.setup();
            OnOff.setup();
            $('#last-update').html(data['last-update']);
        });
    }

    function refresh() {
        $.ajax({
            type: 'POST',
            url: '/rest/users',
            data: {'action': 'refresh'},
            dataType: 'json',
            async: false,

            success: function(data) {
                update(data);
            },
            error: common.ajaxError,
        });
    }

    function bind_refresh() {
        $('.refresh > i').bind('click', function() {
            if (active) {
                refresh();
            }
        });
    }

    function query(letter) {
        var url = '/rest/users';
        if (letter != null) {
            url += '?startswith=' + letter;
        }
        $.ajax({
            url: url,
            success: function(data) {
                startswith = letter;
                update(data);
            },
            error: common.ajaxError,
        });
    }

    topic.subscribe('state', function(message, data) {
        $().ready(function() {
            var allowed = data['allowable-actions'];
            if ($.inArray('user-refresh', allowed) >= 0) {
                $('.refresh > i').removeClass('inactive');
                $('.refresh > p > span.message').html('');
                active = true;
                bind_refresh();
            } else {
                $('.refresh > i').addClass('inactive');
                $('.refresh > i').off('click');
                $('.refresh > p > span.message').html(refresh_unavailable_text);
                active = false;
            }
            $('.refresh p').show();
        });
    });

    common.startMonitor(false);
    query();

    $().ready(function() {
        var html = '';        
	for(var i=0; i<LETTERS.length; i++)
	{
            if (i > 0) {
                html += "&nbsp;:\n";
            }
	    html += "<a>" + LETTERS.charAt(i) + "</a>";
        }
        $('.letters').html(html + "\n");
        $('.letters a').bind('click', function() {
            query($(this).html());
        });
    });
});
