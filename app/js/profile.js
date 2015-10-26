require(['jquery', 'common', 'EditBox', 'plugin', 'OnOff', 'bootstrap'],
        function ($, common, EditBox, plugin, OnOff)
{
    common.startMonitor(false);

    $().ready(function() {
        EditBox.setup();
        OnOff.setup();
    });
});
