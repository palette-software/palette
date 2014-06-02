require(['jquery', 'template', 'common', 'bootstrap'],
function ($, template, common)
{
    function update(data) {
        $().ready(function() {
            var t = $('#user-list-template').html();
            var rendered = template.render(t, data);
            $('#user-list').html(rendered);
            common.bindEvents();
            common.setupDropdowns();
        });
    }

    $.ajax({
        url: '/rest/users',
        success: function(data) {
            update(data);
        },
        error: function(req, textStatus, errorThrown) {
            console.log('[ERROR] '+textStatus+': '+errorThrown);
        }
    });

    common.startup();
});
