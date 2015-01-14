define(['jquery'],
function ($)
{
    /*
     * gatherEmailData()
     * Get all of the input data for email setup and return a dict.
     */
    function gatherEmailData() {
        var fields = ['alert-email-name', 'alert-email-address',
                      'smtp-server', 'smtp-port',
                      'smtp-username', 'smtp-password']

        var data = {}
        for (var index = 0; index < fields.length; index++) {
            data[fields[index]] = $('#' + fields[index]).val();
        };
        data['mail-server-type'] = $('#mail-server-type > button > div').attr('data-id');
        data['enable-tls'] = $('#enable-tls .onoffswitch-checkbox').prop("checked");
        return data;
    }

    return {'gatherEmailData': gatherEmailData}
});
