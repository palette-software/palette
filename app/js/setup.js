require(['jquery', 'underscore', 'configure', 'common',
         'Dropdown', 'OnOff', 'bootstrap'],
function ($, _, configure, common, Dropdown, OnOff)
{
    var urlData = null;
    var tableauURLData = null;
    var mailData = null;
    var sslData = null;
    var tzData = null;
    var authData = null;
    var readOnlyData = null;

    /*
     * maySaveURL()
     * Return true if the 'Server URL' section has changed and is valid.
     */
    function maySaveURL(data)
    {
        var server_url = data['server-url'];
        if (common.validURL(server_url)
            && (server_url != urlData['server-url']))
        {
            return true;
        }

        return false;
    }

    /*
     * mayCancelURL()
     * Return true if 'Server URL' section has changed.
     */
    function mayCancelURL(data)
    {
        var server_url = data['server-url'];
        if (server_url != urlData['server-url'])
        {
            return true;
        }
        return false;
    }

    /*
     * saveURL()
     * Callback for the 'Save' button in the Server URL section.
     */
    function saveURL() {
        $('#save-url, #cancel-url').addClass('disabled');
        var data = configure.gatherURLData();
        data['action'] = 'save';

        $.ajax({
            type: 'POST',
            url: '/rest/setup/url',
            data: data,
            dataType: 'json',
            async: false,

            success: function() {
                delete data['action'];
                urlData = data;
            },
            error: function (jqXHR, textStatus, errorThrown) {
                alert(this.url + ": " +
                      jqXHR.status + " (" + errorThrown + ")");
            }
        });

        validate();
    }

    /*
     * cancelURL()
     * Callback for the 'Cancel' button in the Server URL section.
     */
    function cancelURL()
    {
        $('#server-url').val(urlData['server-url']);
        $('#save-url, #cancel-url').addClass('disabled');
        validate();
    }

    /*
     * maySaveTableauURL()
     * Return true if the 'Tableau Server URL' section has changed and is valid.
     */
    function maySaveTableauURL(data)
    {
        var server_url = data['tableau-server-url'];
        if (common.validURL(server_url)
            && (server_url != tableauURLData['tableau-server-url']))
        {
            return true;
        }

        return false;
    }

    /*
     * mayCancelTableauURL()
     * Return true if 'TableauServer URL' section has changed.
     */
    function mayCancelTableauURL(data)
    {
        var server_url = data['tableau-server-url'];
        if (server_url != tableauURLData['tableau-server-url'])
        {
            return true;
        }
        return false;
    }

    /*
     * saveTableauURL()
     * Callback for the 'Save' button in the Server URL section.
     */
    function saveTableauURL() {
        $('#save-tableau-url, #cancel-tableau-url').addClass('disabled');
        var data = configure.gatherTableauURLData();
        data['action'] = 'save';

        $.ajax({
            type: 'POST',
            url: '/rest/setup/tableau-url',
            data: data,
            dataType: 'json',
            async: false,

            success: function() {
                delete data['action'];
                tableauURLData = data;
            },
            error: function (jqXHR, textStatus, errorThrown) {
                alert(this.url + ": " +
                      jqXHR.status + " (" + errorThrown + ")");
            }
        });

        validate();
    }

    /*
     * cancelTableauURL()
     * Callback for the 'Cancel' button in the Tableau Server URL section.
     */
    function cancelTableauURL()
    {
        $('#tableau-server-url').val(tableauURLData['tableau-server-url']);
        $('#save-tableau-url, #cancel-tableau-url').addClass('disabled');
        validate();
    }

    /*
     * mayCancelAdmin()
     * Return true if 'Palette Admin' section has changed.
     */
    function mayCancelAdmin(data)
    {
        var password = data['password'];
        if (data['password'].length > 0)
        {
            return true;
        }
        if (data['confirm-password'].length > 0)
        {
            return true;
        }
        return false;
    }

    /*
     * saveAdmin()
     * Callback for the 'Save' button in the 'Admin Password' section.
     */
    function saveAdmin() {
        $('#save-admin, #cancel-admin').addClass('disabled');
        data = configure.gatherAdminData();
        data['action'] = 'save';
        delete data['confirm-password'];

        var result = null;
        $.ajax({
            type: 'POST',
            url: '/rest/setup/admin',
            data: data,
            dataType: 'json',
            async: false,

            success: function() {
                $('#password, #confirm-password').val('');
            },
            error: function (jqXHR, textStatus, errorThrown) {
                alert(this.url + ": " +
                      jqXHR.status + " (" + errorThrown + ")");
            }
        });
        validate();
    }

    /*
     * cancelAdmin()
     * Callback for the 'Cancel' button in the 'Admin Password' section.
     */
    function cancelAdmin()
    {
        $('#password, #confirm-password').val('');
        $('#save-admin, #cancel-admin').addClass('disabled');
        validate();
    }

    /*
     * saveReadOnly()
     * Callback for the 'Save' button in the 'Tableau Readonly User' section.
     */
    function saveReadOnly() {
        $('#save-readonly, #cancel-readonly').addClass('disabled');
        data = configure.gatherReadOnlyData();
        data['action'] = 'save';

        var result = null;
        $.ajax({
            type: 'POST',
            url: '/rest/setup/readonly',
            data: data,
            dataType: 'json',
            async: false,

            success: function() {
                delete data['action'];
                readOnlyData = data;
            },
            error: function (jqXHR, textStatus, errorThrown) {
                alert(this.url + ": " +
                      jqXHR.status + " (" + errorThrown + ")");
            }
        });
        validate();
    }

    /*
     * cancelReadOnly()
     * Callback for the 'Cancel' button in the 'Tableau Readonly User' section.
     */
    function cancelReadOnly()
    {
        $('#readonly-password').val(readOnlyData['readonly-password']);
        $('#save-readonly, #cancel-readonly').addClass('disabled');
        validate();
    }

    /*
     * maySaveCancelReadOnly()
     * Return true if 'Tableau Readonly User' section has changed.
     */
    function maySaveCancelReadOnly(data)
    {
        return !_.isEqual(data, readOnlyData);
    }

    /*
     * maySaveMail()
     * Return true if the 'Mail Server' section has changed and is valid.
     */
    function maySaveMail(data)
    {
        if (_.isEqual(data, mailData)) {
            return false;
        }
        return configure.validMailData(data);
    }

    /*
     * mayCancelMail()
     * Return true if 'Mail Server' section has changed.
     */
    function mayCancelMail(data)
    {
        return !_.isEqual(data, mailData);
    }

    /*
     * validateMail()
     */
    function validateMail()
    {
        var maySave;
        var testEmailRecipient = $('#test-email-recipient').val();

        var data = configure.gatherMailData();
        if (maySaveMail(data)) {
            $('#save-mail').removeClass('disabled');
            maySave = true;
        } else {
            maySave = false;
            $('#save-mail').addClass('disabled');
        }
        if (mayCancelMail(data)) {
            $('#cancel-mail').removeClass('disabled');
        } else {
            $('#cancel-mail').addClass('disabled');
        }

        if (common.validEmail(testEmailRecipient)) {
            if (_.isEqual(data, mailData)) {
                $('#test-mail').removeClass('disabled');
            } else {
                $('#test-mail').addClass('disabled');
            }
        }
    }

    /*
     * saveMail()
     * Callback for the 'Save' button in the 'Mail Server' section.
     */
    function saveMail() {
        $('#save-mail, #cancel-mail').addClass('disabled');
        var data = configure.gatherMailData();
        data['action'] = 'save';

        var result = null;
        $.ajax({
            type: 'POST',
            url: '/rest/setup/mail',
            data: data,
            dataType: 'json',
            async: false,

            success: function() {
                delete data['action'];
                mailData = data;
                $('#smtp-password').val('');
            },
            error: function (jqXHR, textStatus, errorThrown) {
                alert(this.url + ": " +
                      jqXHR.status + " (" + errorThrown + ")");
            }
        });
        validate();
    }

    /*
     * cancelMail()
     * Callback for the 'Cancel' button in the 'Mail Server' section.
     */
    function cancelMail()
    {
        Dropdown.setValueById('mail-server-type', mailData['mail-server-type']);
        $('#alert-email-name').val(mailData['alert-email-name']);
        $('#alert-email-address').val(mailData['alert-email-address']);
        $('#smtp-server').val(mailData['smtp-server']);
        $('#smtp-port').val(mailData['smtp-port']);
        $('#smtp-username').val(mailData['smtp-username']);
        $('#smtp-password').val('');
        $('#save-mail, #cancel-mail').addClass('disabled');
        $('#mail-test-message').addClass('hidden');
        $('#mail-test-message').removeClass('green red');
        validate();
    }

    /*
     * testMail()
     * Callback for the 'Test Email' button.
     */
    function testMail() {
        $('#mail-test-message').html("");
        $('#mail-test-message').addClass('hidden');
        $('#mail-test-message').removeClass('green red');

        var data = configure.gatherMailData();
        data['test-email-recipient'] = $('#test-email-recipient').val();
        data['action'] = 'test';

        var result = {};
        $.ajax({
            type: 'POST',
            url: '/rest/setup/mail',
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
            $('#mail-test-message').html("OK");
            $('#mail-test-message').addClass('green');
            $('#mail-test-message').removeClass('red hidden');
        } else {
            var html = 'FAILED';
            if (result['error'] != null && result['error'].length > 0) {
                html += ': ' + result['error'];
            }
            $('#mail-test-message').html(html);
            $('#mail-test-message').addClass('red');
            $('#mail-test-message').removeClass('green hidden');
        }
    }

    /*
     * mayCancelSSL()
     * Return true if 'Server SSL' section has changed.
     */
    function mayCancelSSL(data)
    {
        if (!data['enable-ssl']) {
            return false;
        }
        if (data['ssl-certificate-file'].length > 0) {
            return true
        }
        if (data['ssl-certificate-key-file'].length > 0) {
            return true;
        }
         if (data['ssl-certificate-chain-file'].length > 0) {
            return true;
        }
        return false;
    }

    /*
     * saveSSL()
     * Callback for the 'Save' button in the SSL Certificate section.
     */
    function saveSSL() {
        var data = configure.gatherSSLData();
        data['action'] = 'save';

        var result = null;
        $.ajax({
            type: 'POST',
            url: '/rest/setup/ssl',
            data: data,
            dataType: 'json',
            async: false,

            success: function() {
                cancelSSL();
            },
            error: function (jqXHR, textStatus, errorThrown) {
                alert(this.url + ": " +
                      jqXHR.status + " (" + errorThrown + ")");
            }
        });
        validate();
    }

    /*
     * cancelSSL()
     * Callback for the 'Cancel' button in the 'Server SSL' section.
     */
    function cancelSSL()
    {
        OnOff.setValueById('enable-ssl', sslData['enable-ssl']);
        $('#ssl-certificate-file').val('');
        $('#ssl-certificate-key-file').val('');
        $('#ssl-certificate-chain-file').val('');
        $('#save-ssl, #cancel-ssl').addClass('disabled');
        configure.changeSSL();
        validate();
    }

    /*
     * maySaveCancelTz()
     * Return true if the 'Authentication' section has changed.
     */
    function maySaveCancelTz(data)
    {
        return !_.isEqual(data, tzData);
    }

    /*
     * saveTz()
     * Callback for the 'Save' button in the Timezone section.
     */
    function saveTz() {
        var data = configure.gatherTzData();
        data['action'] = 'save';

        $.ajax({
            type: 'POST',
            url: '/rest/setup/tz',
            data: data,
            dataType: 'json',
            async: false,

            success: function() {
                delete data['action'];
                tzData = data;
            },
            error: function (jqXHR, textStatus, errorThrown) {
                alert(this.url + ": " +
                      jqXHR.status + " (" + errorThrown + ")");
            }
        });
        validate();
    }

    /*
     * cancelTz()
     * Callback for the 'Cancel' button in the Timezone section.
     */
    function cancelTz() {
        var id = 'timezone';
        Dropdown.setValueById(id, authData[id]);
        $('#save-tz, #cancel-tz').addClass('disabled');
        validate();
    }

    /*
     * gatherAuthData()
     * Return the current settings in the 'Authentication' section as a dict.
     */
    function gatherAuthData() {
        var data = {};

        var id = 'authentication-type';
        data[id] = Dropdown.getValueById(id);

        return data;
    }

    /*
     * maySaveCancelAuth()
     * Return true if the 'Authentication' section has changed.
     */
    function maySaveCancelAuth(data)
    {
        return !_.isEqual(data, authData);
    }

    /*
     * saveAuth()
     * Callback for the 'Save' button in the Authentication section.
     */
    function saveAuth() {
        var data = gatherAuthData();
        data['action'] = 'save';

        $.ajax({
            type: 'POST',
            url: '/rest/setup/auth',
            data: data,
            dataType: 'json',
            async: false,

            success: function() {
                delete data['action'];
                authData = data;
            },
            error: function (jqXHR, textStatus, errorThrown) {
                alert(this.url + ": " +
                      jqXHR.status + " (" + errorThrown + ")");
            }
        });
        validate();
    }

    /*
     * cancelAuth()
     * Callback for the 'Cancel' button in the Authentication section.
     */
    function cancelAuth() {
        var id = 'authentication-type';
        Dropdown.setValueById(id, authData[id]);
        $('#save-auth, #cancel-auth').addClass('disabled');
        validate();
    }

    /*
     * validate()
     * Enable/disable the buttons based on the field values.
     */
    function validate() {
        configure.validateSection('url', configure.gatherURLData,
                                  maySaveURL, mayCancelURL);
        configure.validateSection('tableau-url', configure.gatherTableauURLData,
                                  maySaveTableauURL, mayCancelTableauURL);
        configure.validateSection('admin', configure.gatherAdminData,
                                  configure.validAdminData, mayCancelAdmin);
        configure.validateSection('readonly', configure.gatherReadOnlyData,
                                  maySaveCancelReadOnly, maySaveCancelReadOnly);
        validateMail();
        configure.validateSection('ssl', configure.gatherSSLData,
                                  configure.validSSLData, mayCancelSSL);
        configure.validateSection('auth', gatherAuthData,
                                  maySaveCancelAuth, maySaveCancelAuth);
        configure.validateSection('tz', configure.gatherTzData,
                                  maySaveCancelTz, maySaveCancelTz);
    }

    /*
     * setup()
     * Enable everything after the REST handler returns.
     */
    function setup(data) {
        Dropdown.setupAll(data);
        OnOff.setup();

        /* URL */
        $('#server-url').val(data['server-url']);
        $('#save-url').bind('click', saveURL);
        $('#cancel-url').bind('click', cancelURL);
        urlData = configure.gatherURLData();

        /* Tableau URL */
        $('#tableau-server-url').val(data['tableau-server-url']);
        $('#save-tableau-url').bind('click', saveTableauURL);
        $('#cancel-tableau-url').bind('click', cancelTableauURL);
        tableauURLData = configure.gatherTableauURLData();

        /* Admin */
        $('#save-admin').bind('click', saveAdmin);
        $('#cancel-admin').bind('click', cancelAdmin);

        /* Readonly User */
        $('#readonly-password').val(data['readonly-password']);
        $('#save-readonly').bind('click', saveReadOnly);
        $('#cancel-readonly').bind('click', cancelReadOnly);
        readOnlyData = configure.gatherReadOnlyData();

        /* Mail */
        $('#alert-email-name').val(data['alert-email-name']);
        $('#alert-email-address').val(data['alert-email-address']);
        $('#smtp-server').val(data['smtp-server']);
        $('#smtp-port').val(data['smtp-port']);
        $('#smtp-username').val(data['smtp-username']);
        $('#smtp-password').val(data['smtp-password']);
        $('#save-mail').bind('click', saveMail);
        $('#cancel-mail').bind('click', cancelMail);
        $('#test-mail').bind('click', testMail);
        mailData = configure.gatherMailData();
        configure.changeMail();

        /* SSL */
        $('#enable-ssl').val(data['enable-ssl']);
        $('#save-ssl').bind('click', saveSSL);
        $('#cancel-ssl').bind('click', cancelSSL);
        sslData = configure.gatherSSLData();
        configure.changeSSL();

        /* Timezone */
        $('#save-tz').off('click');
        $('#save-tz').bind('click', saveTz);
        $('#cancel-tz').bind('click', cancelTz);
        tzData = configure.gatherTzData();

        /* Authentication */
        $('#save-auth').off('click');
        $('#save-auth').bind('click', saveAuth);
        $('#cancel-auth').bind('click', cancelAuth);
        authData = gatherAuthData();

        /* validation */
        Dropdown.setCallback(validate);
        Dropdown.setCallback(function () {
            configure.changeMail();
            validate();
        }, '#mail-server-type');
        OnOff.setCallback(validate);
        OnOff.setCallback(function (checked) {
            configure.changeSSL(checked);
            validate();
        }, '#enable-ssl');
        configure.setInputCallback(validate);
        validate();

        /* help */
        configure.lightbox(236535, 'Palette Server URL');
        configure.lightbox(237794, 'Tableau Server URL');
        configure.lightbox(236536, 'Palette Admin Password');
        configure.lightbox(252063, 'Tableau Server Repository Database User Password');
        configure.lightbox(236542, 'Mail Server');
        configure.lightbox(236543, 'Server SSL Certificate');
        configure.lightbox(236544, 'Authentication');
        configure.lightbox(237785, 'Timezone');
    }

    common.startMonitor(false);
    
    /* fire. */
    $.ajax({
        url: '/rest/setup',
        success: function(data) {
            $().ready(function() {
                setup(data);
            });
        },
        error: common.ajaxError,
    });
});
