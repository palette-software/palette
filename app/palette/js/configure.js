define(['jquery', 'Dropdown', 'OnOff'],
function ($, Dropdown, OnOff)
{
    /*
     * validateSection()
     * Enable/Disable the Save and Cancel buttons on particular section.
     */
    function validateSection(name, gather, maySave, mayCancel)
    {
        var data = gather();
        if (maySave(data)) {
            $('#save-'+name).removeClass('disabled');
        } else {
            $('#save-'+name).addClass('disabled');
        }
        if (mayCancel(data)) {
            $('#cancel-'+name).removeClass('disabled');
        } else {
            $('#cancel-'+name).addClass('disabled');
        }
    }

    return {'validateSection': validateSection}
});
