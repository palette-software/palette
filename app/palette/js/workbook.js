require(['jquery', 'template', 'common', 'EditBox', 'bootstrap'],
function ($, template, common, EditBox)
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
                EditBox.setup();
                // prevent the link from opening/closing the event.
                $('.event > div.summary a').bind('click', function(event) {
                    event.stopPropagation();
                });
            });
        },
        error: common.ajaxError,
    });

    common.startMonitor();
});
