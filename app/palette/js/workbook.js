require(['jquery', 'template', 'common', 'bootstrap'],
function ($, template, common)
{
    var t = $('#workbook-list-template').html();
    template.parse(t);
    
    $.ajax({
        url: '/rest/workbooks',
        success: function(data) {
            $().ready(function() {
               var rendered = template.render(t, data);
               $('#workbook-list').html(rendered);
               common.bindEvents(); /* workbooks have '.event' class */
            });
        },
        error: common.ajaxError,
    });

    common.startMonitor();
});
