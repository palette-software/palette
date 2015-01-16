require(['jquery', 'template', 'configure', 'common',
         'Dropdown', 'OnOff', 'bootstrap'],
function ($, template, configure, common, Dropdown, OnOff)
{

    var urlData = null;
    var authData = null;

    /*
     * clear()
     * Empty all input fields.
     */
    function clear() {
        $('input[type="text"], input[type="password"').val(null);
    }

    /*
     * saveAdmin()
     * Callback for the 'Save' button in the 'Admin Password' section.
     */
    function saveAdmin() {
        var data = {'action': 'save'}
        data['password'] = $('#password').val();

        var result = null;
        $.ajax({
            type: 'POST',
            url: '/rest/setup/admin',
            data: data,
            dataType: 'json',
            async: false,

            success: function(data) {
                result = data;
            },
            error: function (jqXHR, textStatus, errorThrown) {
                alert(this.url + ": " +
                      jqXHR.status + " (" + errorThrown + ")");
                sucess = false;
            }
        });
        /* FIXME: failure case? */
    }

    /*
     * saveMailSettings()
     * Callback for the 'Save' button in the 'Mail Server' section.
     */
    function saveMailSettings() {
        var data = {'action': 'save'}
        $.extend(data, configure.gatherEmailData());

        var result = null;
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
                sucess = false;
            }
        });
        /* FIXME: failure case? */
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
     * validateAuthData()
     * Return frue if the 'Authentication' section has changed,
     *  and return false otherwise.
     */
    function validateAuthData()
    {
        var data = gatherAuthData();
        if (data['authetication-type'] != authData['authentication-type']) {
            return false;
        }
        return true;
    }

    /*
     * saveAuth()
     * Callback for the 'Save' button in the Authentication section.
     */
    function saveAuth() {
        var data = {'action': 'save'}

        var id = 'authentication-type';
        data[id] = Dropdown.getValueById(id);

        $.ajax({
            type: 'POST',
            url: '/rest/setup/auth',
            data: data,
            dataType: 'json',
            async: false,

            success: function(data) {
                authData = data;
            },
            error: function (jqXHR, textStatus, errorThrown) {
                alert(this.url + ": " +
                      jqXHR.status + " (" + errorThrown + ")");
            }
        });
    }

    /*
     * saveSSL()
     * Callback for the 'Save' button in the SSL Certificate section.
     */
    function saveSSL() {
        var data = {'action': 'save'}
        data['enable-ssl'] = OnOff.getValueById('enable-ssl');

        var result = null;
        $.ajax({
            type: 'POST',
            url: '/rest/setup/ssl',
            data: data,
            dataType: 'json',
            async: false,

            success: function(data) {
                result = data;
            },
            error: function (jqXHR, textStatus, errorThrown) {
                alert(this.url + ": " +
                      jqXHR.status + " (" + errorThrown + ")");
                sucess = false;
            }
        });
        /* FIXME: failure case? */
    }

    /*
     * saveURL()
     * Callback for the 'Save' button in the Server URL section.
     */
    function saveURL() {
        var data = {'action': 'save'}
        data['server-url'] = $('#server-url').val();

        $.ajax({
            type: 'POST',
            url: '/rest/setup/url',
            data: data,
            dataType: 'json',
            async: false,

            success: function(data) {
                urlData = data;
            },
            error: function (jqXHR, textStatus, errorThrown) {
                alert(this.url + ": " +
                      jqXHR.status + " (" + errorThrown + ")");
            }
        });
    }

    /*
     * cancel()
     * Callback for the 'Cancel' button.
     */
    function cancel() {
        clear();
        validate();
    }

    /*
     * test()
     * Callback for the 'Test Email' button.
     */
    function test() {
        var fields = ['test-email-recipient',
                      'alert-email-name', 'alert-email-address',
                      'smtp-server', 'smtp-port',
                      'smtp-username', 'smtp-password']

        var data = {'action': 'test'}
        for (var index = 0; index < fields.length; index++) {
            data[fields[index]] = $('#' + fields[index]).val();
        };
        data['mail-server-type'] = $('#mail-server-type > button > div').attr('data-id');
        data['enable-tls'] = $('#enable-tls .onoffswitch-checkbox').prop("checked");

        var result = null;
        $.ajax({
            type: 'POST',
            url: '/rest/setup/email',
            data: data,
            dataType: 'json',
            async: false,

            success: function(data) {
                result = data;
            },
            error: function (jqXHR, textStatus, errorThrown) {
                alert(this.url + ": " +
                      jqXHR.status + " (" + errorThrown + ")");
                sucess = false;
            }
        });
        if (result != null) {
            alert('OK');
        }
    }


    /*
     * save_valid()
     * Test input and return true/false.
     */
    function save_valid() {
        return true;
    }

    /*
     * test_valid()
     * Test input and return true/false.
     */
    function test_valid() {
        var recipient = $('#test-email-recipient').val();
        return common.validEmail(recipient);
    }

    /*
     * validate()
     * Enable/disable the buttons based on the field values.
     */
    function validate() {
        var save_enabled = save_valid();
        if (save_enabled) {
            $('#save-mail-settings').removeClass('disabled');
        } else {
            $('#save-mail-settings').addClass('disabled');
        }

        var test_enabled = test_valid();
        if (test_enabled) {
            $('#test').removeClass('disabled');
        } else {
            $('#test').addClass('disabled');
        }
    }

    /* deprecated */
    $().ready(function() {
        $('#save-url').bind('click', saveURL);
        $('#save-mail-settings').bind('click', saveMailSettings);
        $('#save-ssl').bind('click', saveSSL);
        $('#save-admin').bind('click', saveAdmin);
        $('#cancel').bind('click', cancel);
        $('#test').bind('click', test);
        $('input[type="text"], input[type="password"]').on('paste', function() {
            setTimeout(function() {
                /* validate after paste completes by using a timeout. */
                validate();
            }, 100);
        });
        $('input[type="text"], input[type="password"]').on('keyup', function() {
            validate();
        });
    });

    /*
     * setup()
     * Enable everything after the REST handler returns.
     */
    function setup(data) {
        Dropdown.setupAll(data);
        OnOff.setup();

        $('#save-auth').off('click');
        $('#save-auth').bind('click', saveAuth);
        //$('#cancel-auth').bind('click', cancelAuth);
        authData = gatherAuthData();

        validate();
    }

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
