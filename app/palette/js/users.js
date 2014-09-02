require(['jquery', 'topic', 'template', 'common', 'EditBox', 'OnOff', 'bootstrap'],
function ($, topic, template, common, EditBox, OnOff)
{
    var active = false;

    function ddCallback(node, value) {
        var section = $(node).closest('section');
        section.find('.admin-type').text('Palette '+value);
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
                $('.refresh > span').removeClass('inactive');
                bind();
                active = true;
            } else {
                $('.refresh > span').addClass('inactive');
                $('.refresh > span').off('click');
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
