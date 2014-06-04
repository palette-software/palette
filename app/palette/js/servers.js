require(['jquery', 'template', 'common'],
function ($, template, common)
{
    function update(data) {
        $().ready(function() {
            var t = $('#server-list-template').html();
            var rendered = template.render(t, data);
            $('#server-list').html(rendered);
            common.bindEvents();
        });
    }

    $.ajax({
        url: '/rest/servers',
        success: function(data) {
            update(data);
        },
        error: function(req, textStatus, errorThrown) {
            console.log('[ERROR] '+textStatus+': '+errorThrown);
        }
    });

    common.startMonitor();
});
