require(['jquery', 'common', 'EditBox', 'bootstrap'],
function ($, common, EditBox)
{
    common.startMonitor();

    $().ready(function() {
        EditBox.setup();
    });
});
