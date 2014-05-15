require(['jquery', 'template', 'common'],
function (jquery, template)
{
    var t = $('#workbook-list-template').html();
    template.parse(t);
    
    jquery.ajax({
        url: '/rest/workbooks',
        success: function(data) {
            var rendered = template.render(t, data);
            jquery('#workbook-list').html(rendered);
            /* FIXME */
            $('.event').bind('click', function() {
                $(this).toggleClass('open');
            });
        },
        error: function(req, textStatus, errorThrown) {
            console.log('[workbook] ' + textStatus + ': ' + errorThrown);
        },
    });
});

/* Do this last so that event expansion is bound correctly. */
require(['common']);
