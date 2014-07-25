require(['jquery', 'template', 'common', 'EditBox', 'bootstrap'],
function ($, template, common, EditBox)
{
    function update(data) {
        $().ready(function() {
            common.bindEvents();

            EditBox.setup();
        });
    }

    common.startMonitor();

    $.ajax({
        url: '/rest/s3',
        success: function(data) {
            update(data);
        },
        error: common.ajaxError,
    });
});
