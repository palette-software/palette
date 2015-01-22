require(['jquery', 'underscore', 'configure', 'common',
         'Dropdown', 'OnOff', 'bootstrap'],
function ($, _, configure, common, Dropdown, OnOff)
{
    var emailAlertData = null;

    /*
     * save()
     * Callback for 'Save' when GCS/S3 is selected in 'Storage Location'.
     *  id: either S3 or GCS.
     */
    function save(id) {
        var data = {'action': 'save'}
        data['access-key'] = $('#'+id+'-access-key').val();
        data['secret-key'] = $('#'+id+'-secret-key').val();
        data['url'] = $('#'+id+'-url').val();

        $.ajax({
            type: 'POST',
            url: '/rest/general/storage/'+id,
            data: data,
            dataType: 'json',
            async: false,

            success: function(data) {
            },
            error: function (jqXHR, textStatus, errorThrown) {
                alert(this.url + ": " +
                      jqXHR.status + " (" + errorThrown + ")");
            }
        });
    }

    /*
     * test()
     * Callback for 'Test Connection' in 'Storage Location'.
     *  id: either S3 or GCS.
     */
    function test(id) {
        var data = {'action': 'test'}
        data['access-key'] = $('#'+id+'-access-key').val();
        data['secret-key'] = $('#'+id+'-secret-key').val();
        data['url'] = $('#'+id+'-url').val();

        $.ajax({
            type: 'POST',
            url: '/rest/general/storage/'+id,
            data: data,
            dataType: 'json',
            async: false,

            success: function(data) {
            },
            error: function (jqXHR, textStatus, errorThrown) {
                alert(this.url + ": " +
                      jqXHR.status + " (" + errorThrown + ")");
            }
        });
    }

    /*
     * saveLocal()
     * Callback for 'Save' when 'My Machine' is selected in 'Storage Location'.
     */
    function saveLocal() {
        var data = {'action': 'save'}
        data['storage-destination'] = 'foo'; // FIXME

        $.ajax({
            type: 'POST',
            url: '/rest/general/storage/local',
            data: data,
            dataType: 'json',
            async: false,

            success: function(data) {
            },
            error: function (jqXHR, textStatus, errorThrown) {
                alert(this.url + ": " +
                      jqXHR.status + " (" + errorThrown + ")");
            }
        });
    }

    /*
     * remove()
     * Callback for 'Remove Credentials' in 'Storage Location'.
     *  id: either S3 or GCS.
     */
    function remove(id) {
        var data = {'action': 'remove'}

        $.ajax({
            type: 'POST',
            url: '/rest/general/storage/'+id,
            data: data,
            dataType: 'json',
            async: false,

            success: function(data) {
            },
            error: function (jqXHR, textStatus, errorThrown) {
                alert(this.url + ": " +
                      jqXHR.status + " (" + errorThrown + ")");
            }
        });
    }

    /*
     * changeStorageLocation()
     * Set the value of the 'Storage Location' radio button.
     */
    function changeStorageLocation(value) {
        $('#s3, #gcs, #local').addClass('hidden');
        if (value != 'none') {
            $('#' + value).removeClass('hidden');
        }
    }

    /*
     * gatherEmailAlertData()
     */
    function gatherEmailAlertData()
    {
        return {
            'alert-publishers': OnOff.getValueById('alert-publishers'),
            'alert-admins': OnOff.getValueById('alert-admins'),
        };
    }

    /*
     * maySaveCancelEmailAlerts()
     * Return true if the 'Email Alerts' section has changed.
     */
    function maySaveCancelEmailAlerts(data)
    {
        return !_.isEqual(data, emailAlertData);
    }

    /*
     * saveEmailAlerts()
     * Callback for the 'Save' button in the 'Email Alerts' section.
     */
    function saveEmailAlerts() {
        $('#save-email-alerts, #cancel-emails-alerts').addClass('disabled');
        var data = gatherEmailAlertData();
        data['action'] = 'save';

        $.ajax({
            type: 'POST',
            url: '/rest/general/email/alerts',
            data: data,
            dataType: 'json',
            async: false,

            success: function() {
                delete data['action'];
                emailAlertsData = data;
            },
            error: function (jqXHR, textStatus, errorThrown) {
                alert(this.url + ": " +
                      jqXHR.status + " (" + errorThrown + ")");
            }
        });

        validate();
    }

    /*
     * cancelEmailAlerts()
     * Callback for the 'Cancel' button in the 'Email Alerts' section.
     */
    function cancelEmailAlerts()
    {
        OnOff.setValueById('alert-publishers',
                           emailAlertData['alert-publishers']);
        OnOff.setValueById('alert-admins',
                           emailAlertData['alert-admins']);
        $('#save-email-alerts, #cancel-email-alerts').addClass('disabled');
    }

    /*
     * validate()
     * Enable/disable the buttons based on the field values.
     */
    function validate() {
        configure.validateSection('email-alerts', gatherEmailAlertData,
                                  maySaveCancelEmailAlerts,
                                  maySaveCancelEmailAlerts);
    }

    /* deprecated */
    function update(data) {
        /* populate the dropdowns */
        var checked = data['storage-encrypt'];
        $("#storage-encrypt .onoffswitch-checkbox").prop("checked", checked);

        checked = data['workbooks-as-twb'];
        $("#workbook-as-twb .onoffswitch-checkbox").prop("checked", checked);

        var config = data['config'];
        if (config == null) return;

        for (var i in config) {
            var data = config[i];
            var name = data['name'];

            //var rendered = template.render(dropdown_template, data);
            //$('#'+name).html(rendered);
        }
    }

    function setup(data) {
        Dropdown.setupAll(data);
        OnOff.setup();

        /* Storage */
        $('#save-s3').bind('click', function() {save('s3');});
        $('#test-s3').bind('click', function() {test('s3');});
        $('#remove-s3').bind('click', function() {remove('s3');});

        $('#save-gcs').bind('click', function() {save('gcs');});
        $('#test-gcs').bind('click', function() {test('gcs');});
        $('#remove-gcs').bind('click', function() {remove('gcs');});

        $('#save-local').bind('click', saveLocal);

        $('input:radio[name="storage-type"]').change(function() {
            changeStorageLocation($(this).val());
        });
        $('#storage-'+data['storage-type']).prop('checked', true);
        changeStorageLocation(data['storage-type']);

        /* Email Alerts */
        OnOff.setValueById('alert-publishers', data['alert-publishers']);
        OnOff.setValueById('alert-admins', data['alert-admins']);
        $('#save-email-alerts').bind('click', saveEmailAlerts);
        $('#cancel-email-alerts').bind('click', cancelEmailAlerts);
        OnOff.setCallback('#alert-publishers, #alert-admins', validate);
        emailAlertData = gatherEmailAlertData();

         /* validation */
        $('input[type="text"], input[type="password"], textarea').on('paste', function() {
            setTimeout(function() {
                /* validate after paste completes by using a timeout. */
                validate();
            }, 100);
        });
        $('input[type="text"], input[type="password"], textarea').on('keyup', function() {
            validate();
        });

        validate();
    }

    common.startMonitor(false);

    /* fire. */
    $.ajax({
        url: '/rest/general',
        success: function(data) {
            $().ready(function() {
                setup(data);
            });
        },
        error: common.ajaxError,
    });
});
