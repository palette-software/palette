require(['jquery', 'template', 'common', 'EditBox', 'OnOff', 'bootstrap'],
function ($, template, common, EditBox, OnOff)
{
    EditBox.setup();
    OnOff.setup();
    common.startMonitor();
});
