require(['jquery', 'template', 'common', 'domReady!'],
function (jquery, template, common)
{
    var t = jquery('#yml-list-template').html();
    template.parse(t);

    function update(data) {
        $().ready(function() {
            var rendered = template.render(t, data);
            $('#yml-list').html(rendered);
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
