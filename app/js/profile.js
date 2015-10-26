require(['jquery', 'common', 'EditBox', 'OnOff', 'bootstrap'],
function ($, common, EditBox, OnOff)
{
    EditBox.setup();
    OnOff.setup();
    common.startMonitor();
});
