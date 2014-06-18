require(['jquery', 'template', 'common', 'EditBox', 'bootstrap'],
function ($, template, common, EditBox)
{
    function update(data) {
        $().ready(function() {
            var t = $('#user-list-template').html();
            var rendered = template.render(t, data);
            $('#user-list').html(rendered);
            common.bindEvents();
            common.setupDropdowns();
            EditBox.setup();
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

    common.startMonitor();

    $.ajax({
        url: '/rest/users',
        success: function(data) {
            update(data);
        },
        error: common.ajaxError,
    });

    $().ready(function() {
        $('.refresh > span').bind('click', function() {
            refresh();
        });
    });

});
