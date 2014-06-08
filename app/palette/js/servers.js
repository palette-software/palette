require(['jquery', 'template', 'common', 'EditBox'],
function ($, template, common, EditBox)
{
    function update(data) {
        $().ready(function() {
            var t = $('#server-detail-template').html();
            var rendered = template.render(t, data);
            $('#server-detail').html(rendered);
            common.bindEvents();
            EditBox.bind('.editbox.displayname');
            EditBox.bind('.editbox.environment', function(value) {
                $('.editbox.environment >span').html(value);
            });
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
