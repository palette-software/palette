require(['jquery', 'template', 'common'],
function (jquery, template)
{
    var t = $('#extract-list-template').html();
    template.parse(t);
    
    jquery.ajax({
        url: '/rest/extracts',
        success: function(data) {
            var rendered = template.render(t, data);
            jquery('#extract-list').html(rendered);
            /* FIXME */
            $('.event').bind('click', function() {
                $(this).toggleClass('open');
            });
        },
        error: function(req, textStatus, errorThrown) {
            console.log('[extract] ' + textStatus + ': ' + errorThrown);
        },
    });
});
