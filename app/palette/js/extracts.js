require(['jquery', 'template', 'common', 'bootstrap'],
function ($, template, common)
{
    var t = $('#extract-list-template').html();
    template.parse(t);
    
    $.ajax({
        url: '/rest/extracts',
        success: function(data) {
            $().ready(function() {
                var rendered = template.render(t, data);
                $('#extract-list').html(rendered);
                common.bindEvents(); /* extracts have the '.event' class */
            });
        },
        error: function(req, textStatus, errorThrown) {
            console.log('[extract] ' + textStatus + ': ' + errorThrown);
        },
    });

    common.startMonitor();
});
