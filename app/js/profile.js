require(['jquery', 'common', 'OnOff', 'EditBox'],
        function ($, common, OnOff, EditBox)
{
    common.startMonitor(false);

    $().ready(function() {
        EditBox.setup();
        OnOff.setup();
    });
});
