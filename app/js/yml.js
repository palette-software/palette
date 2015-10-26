require(['jquery', 'common'],
function ($, common)
{
    function update(data) {
        $().ready(function() {
            var count = data["items"].length;
            if (count == 0) {
                $('#yml-list div').removeClass("hidden");
                return;
            }
            $('#yml-list').render('yml-list-template', data);

            var location = data['location'];
            if (location != null) {
                $('#location').html(location);
            }

            var last_update = data['last-update'];
            if (last_update != null) {
                $('#last-update').html(last_update);
                $('.refresh').show();
            }
        });
    }

    $.ajax({
        url: '/rest/yml',
        success: function(data) {
            update(data);
        },
        error: common.ajaxError,
    });

    common.startMonitor(false);
});
