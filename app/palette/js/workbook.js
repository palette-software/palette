require(['jquery', 'template', 'common', 'bootstrap', 'domReady!'],
function (jquery, template, common)
{
    var t = $('#workbook-list-template').html();
    template.parse(t);
    
    jquery.ajax({
        url: '/rest/workbooks',
        success: function(data) {
            var rendered = template.render(t, data);
            jquery('#workbook-list').html(rendered);
            common.bindEvents(); /* workbooks have '.event' class */
        },
        error: function(req, textStatus, errorThrown) {
            console.log('[workbook] ' + textStatus + ': ' + errorThrown);
        },
    });

    common.startup();
});
