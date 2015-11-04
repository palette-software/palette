require(['jquery', 'topic', 'common', 'Dropdown', 'OnOff'],
function ($, topic, common, Dropdown, OnOff)
{
    var LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ";

    var active = false;
    var refresh_unavailable_text = 'Refresh not currently possible.';

    var startswith = null;
    var counts = null;

    function ddCallback(id, value) {
        var $item = $(this.node).closest('.item');
        var $display_role = $('.display-role', $item);
        var old = $display_role.html();
        if (/Publisher/i.test(old)) {
            if (value.toLowerCase() == 'none') {
                value = 'Publisher';
            } else {
                value = 'Publisher & ' + value;
            }
        }
        $('.display-role', $item).html(value);
    }

    function setup_letters(total) {
        
        var html = '';
        if (total <= 100) {
            html = '<a>All</a>';
        }
	    for(var i=0; i<LETTERS.length; i++)
	    {
            var letter = LETTERS.charAt(i);
            if (!(letter in counts)) {
                continue;
            }
            if (html.length > 0) {
                html += "&nbsp;:\n";
            }
	        html += "<a>" + LETTERS.charAt(i) + "</a>";
        }
        $('.letters').html(html + "\n");
        $('.letters a').bind('click', function() {
            query($(this).html());
        });
    }

    function update(data) {
        $().ready(function() {

            counts = data['counts']
            var total = counts['__total__']
            if (total == 0) {
                $('#user-list div').removeClass("hidden");
                return;
            }

            $('#user-list').render('user-list-template', data);
            setup_letters(total);

            Dropdown.bind('.admin-type', data['admin-levels'], ddCallback);
            $('.admin-type').each(function() {
                var dd = $(this).data();
                dd.set(parseInt(dd.original_html));
            });
            OnOff.setup();

            var last_update = data['last-update']
            if (last_update != null) {
                $('#last-update').html(last_update);
                $('.refresh').show();
            }
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
        $('.refresh > p > i').bind('click', function() {
            if (active) {
                refresh();
            }
        });
    }

    function query(val) {
        var url = '/rest/users';
        if (val != null && val.toLowerCase() != 'all') {
            url += '?startswith=' + val;
        }
        $.ajax({
            url: url,
            success: function(data) {
                if (val != null && val.toLowerCase() != 'all') {
                    startswith = val;
                }
                update(data);
            },
            error: common.ajaxError,
        });
    }

    topic.subscribe('state', function(message, data) {
        $().ready(function() {
            var allowed = data['allowable-actions'];
            if ($.inArray('user-refresh', allowed) >= 0) {
                $('.refresh > p > i').removeClass('inactive');
                $('.refresh > p > span.message').html('');
                active = true;
                bind_refresh();
            } else {
                $('.refresh > p > i').addClass('inactive');
                $('.refresh > p > i').off('click');
                $('.refresh > p > span.message').html(refresh_unavailable_text);
                active = false;
            }
        });
    });

    common.startMonitor(false);
    query();
});
