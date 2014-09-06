require(['jquery', 'topic', 'template', 'common', 'EditBox', 'OnOff', 'bootstrap'],
function ($, topic, template, common, EditBox, OnOff)
{
    var active = false;
    var refresh_unavailable_text = 'Refresh not currently possible.';

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
            $('.refresh p').show();
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

    function bind() {
        $('.refresh > span').bind('click', function() {
            if (active) {
                refresh();
            }
        });
    }

    topic.subscribe('state', function(message, data) {
        $().ready(function() {
            var allowed = data['allowable-actions'];
            if ($.inArray('user-refresh', allowed) >= 0) {
                $('.refresh > span.fa-stack').removeClass('inactive');
                $('.refresh > p > span.message').html('');
                active = true;
                bind();
            } else {
                $('.refresh > span.fa-stack').addClass('inactive');
                $('.refresh > span.fa-stack').off('click');
                $('.refresh > p > span.message').html(refresh_unavailable_text);
                active = false;
            }
        });
    });

    common.startMonitor(false);

    $.ajax({
        url: '/rest/users',
        success: function(data) {
            update(data);
        },
        error: common.ajaxError,
    });
});
