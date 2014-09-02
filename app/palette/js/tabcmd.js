require(['jquery', 'template', 'common', 'EditBox', 'bootstrap', 'domReady!'],
function ($, template, common, EditBox)
{
    EditBox.setup();
    common.startMonitor(false);
});
