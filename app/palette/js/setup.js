require(['jquery', 'underscore', 'configure', 'common',
         'Dropdown', 'OnOff', 'bootstrap'],
function ($, _, configure, common, Dropdown, OnOff)
{

    var MAIL_DIRECT = 1;
    var MAIL_RELAY = 2;
    var MAIL_NONE = 3;

    var urlData = null;
    var mailData = null;
    var authData = null;

    /*
     * gatherURLData()
     */
    function gatherURLData()
    {
        return {'server-url': $('#server-url').val()};
    }

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
        var data = gatherURLData();
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
    }

    /*
     * gatherAdminData()
     */
    function gatherAdminData()
    {
        return {
            'password': $('#password').val(),
            'confirm-password': $('#confirm-password').val(),
        }
    }

    /*
     * maySaveURL()
     * Return true if the 'Palette Admin' section has changed and is valid.
     */
    function maySaveAdmin(data)
    {
        var password = data['password'];
        if (common.validPassword(password)
            && (password == data['confirm-password']))
        {
            return true;
        }

        return false;
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
        data = gatherAdminData();
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
    }

    /*
     * gatherMailData()
     */
    function gatherMailData()
    {
        var type = Number(Dropdown.getValueById('mail-server-type'));
        if (type == MAIL_NONE) {
            return {'mail-server-type': type};
        }
        if (type == MAIL_DIRECT) {
            return {
                'mail-server-type': type,
                'alert-email-name': $('#alert-email-name').val(),
                'alert-email-address': $('#alert-email-address').val()
            };
        }
        return {
            'mail-server-type': type,
            'alert-email-name': $('#alert-email-name').val(),
            'alert-email-address': $('#alert-email-address').val(),
            'smtp-server': $('#smtp-server').val(),
            'smtp-port': Number($('#smtp-port').val()),
            'smtp-username': $('#smtp-username').val(),
            'smtp-password': $('#smtp-password').val(),
            'enable-tls': OnOff.getValueById('enable-tls')
        };
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

        var type = Number(Dropdown.getValueById('mail-server-type'));
        if (type == MAIL_NONE) {
            /* Getting here implies mail server type changed. */
            return true;
        }
        /*
         * allow alert-email.name to be unspecified.
        if (data['alert-email-name'].length == 0) {
            return false;
        }
        */
        if (!common.validEmail(data['alert-email-address'])) {
            return false;
        }

        if (type == MAIL_DIRECT) {
            return true;
        }

        if (data['smtp-server'].length == 0) {
            return false;
        }
        if (isNaN(data['smtp-port'])) {
            return false;
        }

        /* SMTP username and password are optional */
        if (data['smtp-username'].length > 0
            && data['smtp-password'].length == 0) {
            return false;
        }
        return true;
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

        var data = gatherMailData();
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
            if (maySave || _.isEqual(data, mailData)) {
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
        var data = gatherMailData();
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
    }

    /*
     * testMail()
     * Callback for the 'Test Email' button.
     */
    function testMail() {
        var data = gatherMailData();
        data['test-email-recipient'] = $('#test-email-recipient').val();
        data['action'] = 'test';

        var result = null;
        $.ajax({
            type: 'POST',
            url: '/rest/setup/mail/test',
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
        if (result != null) {
            alert('OK');
        }
    }

    /*
     * changeMail()
     * Callback for the 'Mail Server Type' dropdown.
     */
    function changeMail()
    {
        var value = Number(Dropdown.getValueById('mail-server-type'));
        if (value == MAIL_NONE) {
            $(".mail-setting").addClass('hidden');
        } else {
            $(".mail-setting").removeClass('hidden');
            if (value == MAIL_DIRECT) {
                $(".smtp").addClass('hidden');
            }
        }
        validateMail()
    }

    /*
     * gatherSSLData()
     */
    function gatherSSLData()
    {
        return {
            'ssl-certificate-file': $('#ssl-certificate-file').val(),
            'ssl-certificate-key-file': $('#ssl-certificate-key-file').val(),
            'ssl-certificate-chain-file': $('#ssl-certificate-chain-file').val()
        }
    }

    /*
     * maySaveSSL()
     * Return true if the 'Server SSL' section has changed and is valid.
     */
    function maySaveSSL(data)
    {
        if (data['ssl-certificate-file'].length == 0) {
            return false;
        }
        if (data['ssl-certificate-key-file'].length == 0) {
            return false;
        }
        return true;
    }

    /*
     * mayCancelSSL()
     * Return true if 'Server SSL' section has changed.
     */
    function mayCancelSSL(data)
    {
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
        var data = gatherSSLData();
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
    }

    /*
     * cancelSSL()
     * Callback for the 'Cancel' button in the 'Server SSL' section.
     */
    function cancelSSL()
    {
        $('#ssl-certificate-file').val('');
        $('#ssl-certificate-key-file').val('');
        $('#ssl-certificate-chain-file').val('');
        $('#save-ssl, #cancel-ssl').addClass('disabled');
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
    }

    /*
     * validate()
     * Enable/disable the buttons based on the field values.
     */
    function validate() {
        configure.validateSection('url', gatherURLData,
                                  maySaveURL, mayCancelURL);
        configure.validateSection('admin', gatherAdminData,
                                  maySaveAdmin, mayCancelAdmin);
        validateMail();
        configure.validateSection('ssl', gatherSSLData,
                                  maySaveSSL, mayCancelSSL);
        configure.validateSection('auth', gatherAuthData,
                                  maySaveCancelAuth, maySaveCancelAuth);
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
        urlData = gatherURLData();

        /* Admin */
        $('#save-admin').bind('click', saveAdmin);
        $('#cancel-admin').bind('click', cancelAdmin);

        /* Mail */
        $('#alert-email-name').val(data['alert-email-name']);
        $('#alert-email-address').val(data['alert-email-address']);
        $('#smtp-server').val(data['smtp-server']);
        $('#smtp-port').val(data['smtp-port']);
        $('#smtp-username').val(data['smtp-username']);
        $('#save-mail').bind('click', saveMail);
        $('#cancel-mail').bind('click', cancelMail);
        $('#test-mail').bind('click', testMail);
        mailData = gatherMailData();
        changeMail();

        /* SSL */
        $('#save-ssl').bind('click', saveSSL);
        $('#cancel-ssl').bind('click', cancelSSL);

        /* Authentication */
        $('#save-auth').off('click');
        $('#save-auth').bind('click', saveAuth);
        $('#cancel-auth').bind('click', cancelAuth);
        authData = gatherAuthData();

        /* validation */
        Dropdown.setCallback(validate);
        Dropdown.setCallback(changeMail, '#mail-server-type');

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
        url: '/rest/setup',
        success: function(data) {
            $().ready(function() {
                setup(data);
            });
        },
        error: common.ajaxError,
    });
});
