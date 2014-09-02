require(['jquery', 'common', 'EditBox', 'bootstrap'],
function ($, common, EditBox)
{
    common.startMonitor(false);

    $().ready(function() {
        EditBox.setup();
    });
});
