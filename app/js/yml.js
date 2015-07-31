require(['jquery', 'template', 'common', 'domReady!'],
function (jquery, template, common)
{
    var t = jquery('#yml-list-template').html();
    template.parse(t);

    function update(data) {
        $().ready(function() {
            var count = data["items"].length;
            if (count == 0) {
                $('#yml-list div').removeClass("hidden");
                return;
            }

            var rendered = template.render(t, data);
            $('#yml-list').html(rendered);

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

    jquery.ajax({
        url: '/rest/yml',
        success: function(data) {
            update(data);
        },
        error: common.ajaxError,
    });

    common.startMonitor(false);
});
