require(['jquery', 'underscore', 'configure', 'common',
         'Dropdown', 'OnOff', 'bootstrap'],
function ($, _, configure, common, Dropdown, OnOff)
{
    var MONITOR_DROPDOWN_IDS = ['disk-watermark-low', 'disk-watermark-high',
                                'cpu-load-warn', 'cpu-period-warn',
                                'cpu-load-error', 'cpu-period-error',
                                'http-load-warn', 'http-load-error'];

    var storageLocation = null;
    var localData = null;
    var s3Data = null;
    var gcsData = null;
    var emailAlertData = null;
    var backupData = null;
    var ziplogData = null;
    var workbookData = null;
    var monitorData = null;

    /*
     * changeStorageLocation()
     * Set the value of the 'Storage Location' radio button.
     */
    function changeStorageLocation(value) {
        $('#s3, #gcs, #local').addClass('hidden');
        $('#' + value).removeClass('hidden');
        validate();
        storageLocation = value;
    }

    /*
     * getData()
     * Get either the S3 or GCS data.
     */
    function getData(name)
    {
        return {
            'access-key': $('#'+name+'-access-key').val(),
            'secret-key': $('#'+name+'-secret-key').val(),
            'url': $('#'+name+'-url').val()
        }
    }

    /*
     * setData()
     * Set either the S3 or GCS data.
     */
    function setData(name, data)
    {
        $('#'+name+'-access-key').val(data[name+'-access-key']);
        $('#'+name+'-secret-key').val(data[name+'-secret-key']);
        $('#'+name+'-url').val(data[name+'-url']);
    }

    /*
     * resetTestMessage()
     * Hide the test message paragraph.
     */
    function resetTestMessage(name)
    {
        $('#'+name+'-test-message').html("");
        $('#'+name+'-test-message').addClass('hidden');
        $('#'+name+'-test-message').removeClass('green red');
    }

    /*
     * resetTestMessage()
     * Hide the test message paragraph.
     */
    function resetTestMessages()
    {
        resetTestMessage('s3');
        resetTestMessage('gcs');
    }

    /*
     * save()
     * Callback for 'Save' when GCS/S3 is selected in 'Storage Location'.
     *  id: either S3 or GCS.
     */
    function save(id) {
        $('#'+id+'-save', '#'+id+'-cancel').addClass('disabled');

        var data = getData(id);
        data['action'] = 'save';

        $.ajax({
            type: 'POST',
            url: '/rest/general/storage/'+id,
            data: data,
            dataType: 'json',
            async: false,

            success: function(returnData) {
                delete data['action'];
                if (id == 's3') {
                    data['url'] = returnData['s3-url'];
                    s3Data = data;
                } else if (id == 'gcs') {
                    data['url'] = returnData['gcs-url'];
                    gcsData = data;
                }
                $('#'+id+'-url').val(data['url']);
            },
            error: function (jqXHR, textStatus, errorThrown) {
                alert(this.url + ": " +
                      jqXHR.status + " (" + errorThrown + ")");
            }
        });

        resetTestMessages();
        validate();
    }

    /*
     * cancel()
     * Callback for 'Cancel' when GCS/S3 is selected in 'Storage Location'.
     *  name: either S3 or GCS.
     */
    function cancel(name, data)
    {
        $('#'+name+'-access-key').val(data['access-key']);
        $('#'+name+'-secret-key').val(data['secret-key']);
        $('#'+name+'-url').val(data['url']);
        resetTestMessages();
        validate();
    }

    /*
     * test()
     * Callback for 'Test Connection' in 'Storage Location'.
     *  id: either S3 or GCS.
     */
    function test(id) {
        $('#'+id+'-save', '#'+id+'-cancel').addClass('disabled');

        var data = {'action': 'test'}
        data['access-key'] = $('#'+id+'-access-key').val();
        data['secret-key'] = $('#'+id+'-secret-key').val();
        data['url'] = $('#'+id+'-url').val();

        var result = {};
        $.ajax({
            type: 'POST',
            url: '/rest/general/storage/'+id,
            data: data,
            dataType: 'json',
            async: false,

            success: function(data) {
                result = data;
            },
            error: function (jqXHR, textStatus, errorThrown) {
                alert(this.url + ": " +
                      jqXHR.status + " (" + errorThrown + ")");
            }
        });

        if (result['status'] == 'OK') {
            $('#'+id+'-test-message').html("OK");
            $('#'+id+'-test-message').addClass('green');
            $('#'+id+'-test-message').removeClass('red hidden');
        } else {
            var html = 'FAILED';
            if (result['error'] != null && result['error'].length > 0) {
                html += ': ' + result['error'];
            }
            $('#'+id+'-test-message').html(html);
            $('#'+id+'-test-message').addClass('red');
            $('#'+id+'-test-message').removeClass('green hidden');
        }
        validate();
    }

    /*
     * remove()
     * Callback for 'Remove Credentials' in 'Storage Location'.
     *  name: either S3 or GCS.
     */
    function remove(name, storedData) {
        var data = {'action': 'remove'}

        $.ajax({
            type: 'POST',
            url: '/rest/general/storage/'+name,
            data: data,
            dataType: 'json',
            async: false,

            success: function(data) {
                $('#'+name+'-access-key').val("");
                $('#'+name+'-secret-key').val("");
                $('#'+name+'-url').val("");
                storedData['access-key'] = '';
                storedData['secret-key'] = '';
                storedData['url'] = '';
            },
            error: function (jqXHR, textStatus, errorThrown) {
                alert(this.url + ": " +
                      jqXHR.status + " (" + errorThrown + ")");
            }
        });

        validate();
    }

    /*
     * maySave()
     * Return true if the S3/GCS section has changed.
     */
    function maySave(data, storedData)
    {
        var location = $('input:radio[name="storage-type"]:checked').val();
        if (_.isEqual(data, storedData) && location == storageLocation) {
            return false;
        }
        if (data['access-key'].length == 0) {
            return false;
        }
        if (data['secret-key'].length == 0) {
            return false;
        }
        if (data['url'].length == 0) {
            return false;
        }
        return true;
    }

    /*
     * mayCancel()
     * Return true if the S3/GCS section can be reset.
     */
    function mayCancel(data, storedData)
    {
        /* Don't compare storage-destination, so can't use isEqual() */
        if (data['access-key'] != storedData['access-key']) {
            return true;
        }
        if (data['secret-key'] != storedData['secret-key']) {
            return true;
        }
        if (data['url'] != storedData['url']) {
            return true;
        }
        return false;
    }

    /*
     * mayTest()
     * Return true if the S3/GCS section can be tested.
     */
    function mayTest(data, storedData)
    {
        if (data['access-key'].length == 0) {
            return false;
        }
        if (data['secret-key'].length == 0) {
            return false;
        }
        if (data['url'].length == 0) {
            return false;
        }
        return true;
    }

    /*
     * mayRemove()
     * Return true if 'Remove Credentials' should be enabled.
     */
    function mayRemove(storedData)
    {
        if (storedData['access-key'].length > 0) {
            return true;
        }
        if (storedData['secret-key'].length > 0) {
            return true;
        }
        if (storedData['url'].length > 0) {
            return true;
        }
        return false;
    }

    /*
     * getLocalData()
     * Return 'My Machine' data.
     */
    function getLocalData() {
        try {
            // FIXME
            var destination = Dropdown.getValueById('storage-destination');
        } catch (e) {
            destination = null;
        }
        return {'storage-destination': destination}
    }

    /*
     * setLocalData()
     */
    function setLocalData(data) {
        var destination = data['storage-destination'];
        if (destination != null) {
            Dropdown.setValueById('storage-destination', destination);
        }
    }

    /*
     * saveLocal()
     * Callback for 'Save' when 'My Machine' is selected in 'Storage Location'.
     */
    function saveLocal() {
        data = getLocalData();
        data['action'] = 'save';

        $.ajax({
            type: 'POST',
            url: '/rest/general/storage/local',
            data: data,
            dataType: 'json',
            async: false,

            success: function() {
                delete data['action'];
                localData = data;
            },
            error: function (jqXHR, textStatus, errorThrown) {
                alert(this.url + ": " +
                      jqXHR.status + " (" + errorThrown + ")");
            }
        });

        validate();
    }

    /*
     * maySaveLocal()
     * Return true if the 'My Machine' section or storage location has changed.
     */
    function maySaveLocal(data)
    {
        var location = $('input:radio[name="storage-type"]:checked').val();
        if (location != storageLocation) {
            return true;
        }
        return !_.isEqual(data, localData);
    }

    /*
     * mayCancelLocal()
     * Return true if the 'My Machine' section has changed.
     */
    function mayCancelLocal(data)
    {
        return !_.isEqual(data, localData);
    }

    /*
     * cancelLocal()
     * Callback for the 'Cancel' button in 'My Machine'.
     */
    function cancelLocal()
    {
        setLocalData(localData);
        $('#save-local, #cancel-local').addClass('disabled');
        validate();
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
                emailAlertData = data;
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
        validate();
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
        validate();
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
        validate();
    }

    /*
     * getWorkbookData()
     */
    function getWorkbookData()
    {
        return {
            'enable-archive': OnOff.getValueById('enable-archive'),
            'archive-username': $('#archive-username').val(),
            'archive-password': $('#archive-password').val(),
            'workbook-retain-count': Dropdown.getValueById('workbook-retain-count'),
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
        Dropdown.setValueById('workbook-retain-count',
                              data['workbook-retain-count']);
    }

    /*
     * maySaveCancelWorkbook()
     * Return true if the 'Workbooks' section has changed and is valid.
     */
    function maySaveWorkbook(data)
    {
        if (_.isEqual(data, workbookData)) {
            return false;
        }
        if ($('#archive-username').val().length == 0) {
            return false;
        }
        if ($('#archive-password').val().length == 0) {
            return false;
        }
        return true;
    }

    /*
     * mayCancelWorkbook()
     * Return true if the 'Workbooks' section has changed.
     */
    function mayCancelWorkbook(data)
    {
        /* FIXME: test for archive-username, archive-password */
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
        changeWorkbooks(workbookData['enable-archive']);
    }

    /*
     * changeWorkbooks()
     * Callback for the 'Archive' On/Off slider.
     */
    function changeWorkbooks(checked)
    {
        if (checked) {
            $('#workbooks div:first').removeClass('hidden');
        } else {
            $('#workbooks div:first').addClass('hidden');
        }
        validate();
    }


    /*
     * getMonitorData()
     */
    function getMonitorData()
    {
        var data = {};
        for (var i = 0; i < MONITOR_DROPDOWN_IDS.length; i++) {
            var id = MONITOR_DROPDOWN_IDS[i];
            data[id] = Dropdown.getValueById(id);
        }
        return data;
    }

    /*
     * setMonitorData()
     */
    function setMonitorData(data)
    {
        OnOff.setValueById('enable-archive', data['enable-archive']);
        for (var i = 0; i < MONITOR_DROPDOWN_IDS.length; i++) {
             var id = MONITOR_DROPDOWN_IDS[i];
             Dropdown.setValueById(id, data[id]);
        }
    }

    /*
     * maySaveCancelMonitor()
     * Return true if the 'Monitors' section has changed.
     */
    function maySaveCancelMonitor(data)
    {
        return !_.isEqual(data, monitorData);
    }

    /*
     * saveMonitors()
     * Callback for the 'Save' button in the 'Monitors' section.
     */
    function saveMonitors() {
        $('#save-monitors, #cancel-monitors').addClass('disabled');
        var data = getMonitorData();
        data['action'] = 'save';

        $.ajax({
            type: 'POST',
            url: '/rest/general/monitor',
            data: data,
            dataType: 'json',
            async: false,

            success: function() {
                delete data['action'];
                monitorData = data;
            },
            error: function (jqXHR, textStatus, errorThrown) {
                alert(this.url + ": " +
                      jqXHR.status + " (" + errorThrown + ")");
            }
        });

        validate();
    }

    /*
     * cancelMonitors()
     * Callback for the 'Cancel' button in the 'Monitors' section.
     */
    function cancelMonitors()
    {
        setMonitorData(monitorData);
        $('#save-monitors, #cancel-monitors').addClass('disabled');
        validate();
    }

    /*
     * validateS3()
     * Enable/Disable the Save and Cancel buttons on S3/GCS sections.
     */
    function validateS3orGCS(name, storedData)
    {
        var data = getData(name);
        if (maySave(data, storedData)) {
            $('#save-'+name).removeClass('disabled');
        } else {
            $('#save-'+name).addClass('disabled');
        }
        if (mayCancel(data, storedData)) {
            $('#cancel-'+name).removeClass('disabled');
        } else {
            $('#cancel-'+name).addClass('disabled');
        }
        if (mayTest(data, storedData)) {
            $('#test-'+name).removeClass('disabled');
        } else {
            $('#test-'+name).addClass('disabled');
        }
        if (mayRemove(storedData)) {
            $('#remove-'+name).removeClass('disabled');
        } else {
            $('#remove-'+name).addClass('disabled');
        }
    }

    /*
     * validate()
     * Enable/disable the buttons based on the field values.
     */
    function validate() {
        configure.validateSection('local', getLocalData,
                                  maySaveLocal, mayCancelLocal);
        validateS3orGCS('s3', s3Data);
        validateS3orGCS('gcs', gcsData);
        configure.validateSection('email-alerts', getEmailAlertData,
                                  maySaveCancelEmailAlerts,
                                  maySaveCancelEmailAlerts);
        configure.validateSection('backups', getBackupData,
                                  maySaveCancelBackup, maySaveCancelBackup);
        configure.validateSection('ziplogs', getZiplogData,
                                  maySaveCancelZiplog, maySaveCancelZiplog);
        configure.validateSection('workbooks', getWorkbookData,
                                  maySaveWorkbook, mayCancelWorkbook);
        configure.validateSection('monitors', getMonitorData,
                                  maySaveCancelMonitor, maySaveCancelMonitor);
    }

    /*
     * setup()
     * Inital setup after the AJAX call returns and the DOM tree is ready.
     */
    function setup(data) {
        Dropdown.setupAll(data);
        OnOff.setup();

        /* Storage location radio button. */
        $('input:radio[name="storage-type"]').change(function() {
            changeStorageLocation($(this).val());
        });
        $('#storage-'+data['storage-type']).prop('checked', true);

        /* My Machine */
        setLocalData(data);
        $('#save-local').bind('click', saveLocal);
        $('#cancel-local').bind('click', cancelLocal);
        localData = getLocalData();

        /* S3/GCS Storage */
        setData('s3', data);
        $('#save-s3').bind('click', function() {save('s3');});
        $('#cancel-s3').bind('click', function() {cancel('s3', s3Data);});
        $('#test-s3').bind('click', function() {test('s3');});
        $('#remove-s3').bind('click', function() {remove('s3', s3Data);});
        s3Data = getData('s3');

        setData('gcs', data);
        $('#save-gcs').bind('click', function() {save('gcs');});
        $('#cancel-gcs').bind('click', function() {cancel('gcs', gcsData);});
        $('#test-gcs').bind('click', function() {test('gcs');});
        $('#remove-gcs').bind('click', function() {remove('gcs', gcsData);});
        gcsData = getData('gcs');

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
        setMonitorData(data);
        $('#save-monitors').bind('click', saveMonitors);
        $('#cancel-monitors').bind('click', cancelMonitors);
        monitorData = getMonitorData();

        /* validation */
        Dropdown.setCallback(validate);
        OnOff.setCallback(validate);
        OnOff.setCallback(changeWorkbooks, '#enable-archive');

        configure.setInputCallback(validate);
        /* implicitly calls validate() */
        changeStorageLocation(data['storage-type']);
        changeWorkbooks(workbookData['enable-archive']);

        /* help */
        configure.lightbox(229204, 'Storage Location');
        configure.lightbox(229207, 'Email Alerts');
        configure.lightbox(229213, 'Backups');
        configure.lightbox(229214, 'Ziplogs');
        configure.lightbox(229215, 'Workbook Archive');
        configure.lightbox(229216, 'Monitoring');
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
