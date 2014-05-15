require(['jquery', 'template', 'common', 'bootstrap', 'domReady!'],
function (jquery, template, common)
{
    var t = $('#extract-list-template').html();
    template.parse(t);
    
    jquery.ajax({
        url: '/rest/extracts',
        success: function(data) {
            var rendered = template.render(t, data);
            jquery('#extract-list').html(rendered);
            common.bindEvents(); /* extracts have the '.event' class */
        },
        error: function(req, textStatus, errorThrown) {
            console.log('[extract] ' + textStatus + ': ' + errorThrown);
        },
    });

    common.startup();
});
