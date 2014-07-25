require(['jquery', 'template', 'common', 'EditBox', 'bootstrap'],
function ($, template, common, EditBox)
{
    function update(data) {
        $().ready(function() {
            common.bindEvents();

            $('#access-key-id').html(data['access-key-id']);
            $('#access-key-secret').html(data['access-key-secret']);
            $('#bucket-name').html(data['bucket-name']);

            EditBox.bind('.editbox');
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
        url: '/rest/s3',
        success: function(data) {
            update(data);
        },
        error: common.ajaxError,
    });

    $().ready(function() {
    });

});
