require(['jquery', 'underscore', 'configure', 'common',
         'Dropdown', 'OnOff', 'bootstrap'],
function ($, _, configure, common, Dropdown, OnOff)
{
    var emailAlertData = null;
    var backupData = null;
    var ziplogData = null;
    var workbookData = null;

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
        $('#' + value).removeClass('hidden');
    }

    /*
     * getEmailAlertData()
     */
    function getEmailAlertData()
    {
        return {
            'alert-publishers': OnOff.getValueById('alert-publishers'),
            'alert-admins': OnOff.getValueById('alert-admins'),
        };
    }

    /*
     * setEmailAlertData()
     */
    function setEmailAlertData(data)
    {
        OnOff.setValueById('alert-publishers', data['alert-publishers']);
        OnOff.setValueById('alert-admins', data['alert-admins']);
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
        var data = getEmailAlertData();
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
        setEmailAlertData(emailAlertData);
        $('#save-email-alerts, #cancel-email-alerts').addClass('disabled');
    }

    /*
     * getBackupData()
     */
    function getBackupData()
    {
        return {
            'scheduled-backups': OnOff.getValueById('scheduled-backups'),
            'backup-auto-retain-count': Dropdown.getValueById('backup-auto-retain-count'),
            'backup-user-retain-count': Dropdown.getValueById('backup-user-retain-count')
        };
    }

    /*
     * setBackupData()
     */
    function setBackupData(data)
    {
        OnOff.setValueById('scheduled-backups', data['scheduled-backups']);
        Dropdown.setValueById('backup-auto-retain-count',
                              data['backup-auto-retain-count']);
        Dropdown.setValueById('backup-user-retain-count',
                              data['backup-user-retain-count']);
    }

    /*
     * maySaveCancelBackup()
     * Return true if the 'Backups' section has changed.
     */
    function maySaveCancelBackup(data)
    {
        return !_.isEqual(data, backupData);
    }

    /*
     * saveBackups()
     * Callback for the 'Save' button in the 'Backups' section.
     */
    function saveBackups() {
        $('#save-backups, #cancel-backups').addClass('disabled');
        var data = getBackupData();
        data['action'] = 'save';

        $.ajax({
            type: 'POST',
            url: '/rest/general/backup',
            data: data,
            dataType: 'json',
            async: false,

            success: function() {
                delete data['action'];
                backupData = data;
            },
            error: function (jqXHR, textStatus, errorThrown) {
                alert(this.url + ": " +
                      jqXHR.status + " (" + errorThrown + ")");
            }
        });

        validate();
    }

    /*
     * cancelBackups()
     * Callback for the 'Cancel' button in the 'Backups' section.
     */
    function cancelBackups()
    {
        setBackupData(backupData);
        $('#save-backups, #cancel-backups').addClass('disabled');
    }

    /*
     * getZiplogData()
     */
    function getZiplogData()
    {
        return {
            'scheduled-ziplogs': OnOff.getValueById('scheduled-ziplogs'),
            'ziplog-auto-retain-count': Dropdown.getValueById('ziplog-auto-retain-count'),
            'ziplog-user-retain-count': Dropdown.getValueById('ziplog-user-retain-count')
        };
    }

    /*
     * setZiplogData()
     */
    function setZiplogData(data)
    {
        OnOff.setValueById('scheduled-ziplogs', data['scheduled-ziplogs']);
        Dropdown.setValueById('ziplog-auto-retain-count',
                              data['ziplog-auto-retain-count']);
        Dropdown.setValueById('ziplog-user-retain-count',
                              data['ziplog-user-retain-count']);
    }

    /*
     * maySaveCancelZiplog()
     * Return true if the 'Ziplogs' section has changed.
     */
    function maySaveCancelZiplog(data)
    {
        return !_.isEqual(data, ziplogData);
    }

    /*
     * saveZiplogs()
     * Callback for the 'Save' button in the 'Ziplogs' section.
     */
    function saveZiplogs() {
        $('#save-ziplogs, #cancel-ziplogs').addClass('disabled');
        var data = getZiplogData();
        data['action'] = 'save';

        $.ajax({
            type: 'POST',
            url: '/rest/general/ziplog',
            data: data,
            dataType: 'json',
            async: false,

            success: function() {
                delete data['action'];
                ziplogData = data;
            },
            error: function (jqXHR, textStatus, errorThrown) {
                alert(this.url + ": " +
                      jqXHR.status + " (" + errorThrown + ")");
            }
        });

        validate();
    }

    /*
     * cancelZiplogs()
     * Callback for the 'Cancel' button in the 'Ziplogs' section.
     */
    function cancelZiplogs()
    {
        setZiplogData(ziplogData);
        $('#save-ziplogs, #cancel-ziplogs').addClass('disabled');
    }

    /*
     * getWorkbookData()
     */
    function getWorkbookData()
    {
        return {
            'enable-archive': OnOff.getValueById('enable-archive'),
            'archive-username': $('#archive-username').val(),
            'archive-password': $('#archive-password').val()
        };
    }

    /*
     * setWorkbookData()
     */
    function setWorkbookData(data)
    {
        OnOff.setValueById('enable-archive', data['enable-archive']);
        $('#archive-username').val(data['archive-username']);
        $('#archive-password').val(data['archive-password']);
    }

    /*
     * maySaveCancelWorkbook()
     * Return true if the 'Workbooks' section has changed.
     */
    function maySaveCancelWorkbook(data)
    {
        return !_.isEqual(data, workbookData);
    }

    /*
     * saveWorkbooks()
     * Callback for the 'Save' button in the 'Workbooks' section.
     */
    function saveWorkbooks() {
        $('#save-workbooks, #cancel-workbooks').addClass('disabled');
        var data = getWorkbookData();
        data['action'] = 'save';

        $.ajax({
            type: 'POST',
            url: '/rest/general/workbook',
            data: data,
            dataType: 'json',
            async: false,

            success: function() {
                delete data['action'];
                workbookData = data;
            },
            error: function (jqXHR, textStatus, errorThrown) {
                alert(this.url + ": " +
                      jqXHR.status + " (" + errorThrown + ")");
            }
        });

        validate();
    }

    /*
     * cancelWorkbooks()
     * Callback for the 'Cancel' button in the 'Workbooks' section.
     */
    function cancelWorkbooks()
    {
        setWorkbookData(workbookData);
        $('#save-workbooks, #cancel-workbooks').addClass('disabled');
    }

    /*
     * validate()
     * Enable/disable the buttons based on the field values.
     */
    function validate() {
        configure.validateSection('email-alerts', getEmailAlertData,
                                  maySaveCancelEmailAlerts,
                                  maySaveCancelEmailAlerts);
        configure.validateSection('backups', getBackupData,
                                  maySaveCancelBackup, maySaveCancelBackup);
        configure.validateSection('ziplogs', getZiplogData,
                                  maySaveCancelZiplog, maySaveCancelZiplog);
        configure.validateSection('workbooks', getWorkbookData,
                                  maySaveCancelWorkbook, maySaveCancelWorkbook);
    }


    /*
     * setup()
     * Inital setup after the AJAX call returns and the DOM tree is ready.
     */
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
        setEmailAlertData(data);
        $('#save-email-alerts').bind('click', saveEmailAlerts);
        $('#cancel-email-alerts').bind('click', cancelEmailAlerts);
        emailAlertData = getEmailAlertData();

        /* Backups */
        setBackupData(data);
        $('#save-backups').bind('click', saveBackups);
        $('#cancel-backups').bind('click', cancelBackups);
        backupData = getBackupData();

        /* Ziplogs */
        setZiplogData(data);
        $('#save-ziplogs').bind('click', saveZiplogs);
        $('#cancel-ziplogs').bind('click', cancelZiplogs);
        ziplogData = getZiplogData();

        /* Workbooks */
        setWorkbookData(data);
        $('#save-workbooks').bind('click', saveWorkbooks);
        $('#cancel-workbooks').bind('click', cancelWorkbooks);
        workbookData = getWorkbookData();

        /* Monitoring */

        OnOff.setCallback(validate);
        Dropdown.setCallback(validate);


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
