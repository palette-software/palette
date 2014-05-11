require.config({
    paths: {
        'jquery': '/app/module/palette/js/vendor/jquery',
        'topic': '/app/module/palette/js/vendor/pubsub',
        'template' : '/app/module/palette/js/vendor/mustache',
        'domReady': '/app/module/palette/js/vendor/domReady',
    }
});

require(['jquery', 'template'],
function (jquery, template)
{
    var t = $('#extract-list-template').html();
    template.parse(t);
    
    jquery.ajax({
        url: '/rest/extracts',
        success: function(data) {
            var rendered = template.render(t, data);
            jquery('#extract-list').html(rendered);
        },
        error: function(req, textStatus, errorThrown) {
            console.log('[extract] ' + textStatus + ': ' + errorThrown);
        },
    });
});

/* Do this last so that event expansion is bound correctly. */
require(['common']);
