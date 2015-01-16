require(['jquery', 'template', 'configure', 'common', 'OnOff', 'bootstrap'],
function ($, template, configure, common, OnOff)
{    
    /*
     * clear()
     * Empty all input fields.
     */
    function clear() {
        $('input[type="text"], input[type="password"').val(null);
    }

    /*
     * saveMailSettings()
     * Callback for the 'Save' button in the Mail Server section.
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
     * Callback for the 'Save' button in the Mail Server section.
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
     * saveAuth()
     * Callback for the 'Save' button in the Authentication section.
     */
    function saveAuth() {
        var data = {'action': 'save'}
        data['authentication-type'] = common.getDropdownValueById('authentication-type');

        var result = null;
        $.ajax({
            type: 'POST',
            url: '/rest/setup/auth',
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

    /* start */
    var dropdown_template = $('#dropdown-template').html();
    template.parse(dropdown_template);

    $().ready(function() {
        $('#save-mail-settings').bind('click', saveMailSettings);
        $('#save-auth').bind('click', saveAuth);
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

    $.ajax({
        url: '/rest/setup',
        success: function(data) {
            $().ready(function() {
                for (var i in data['config']) {
                    var option = data['config'][i];
                    var rendered = template.render(dropdown_template, option);
                    $('#'+option['name']).html(rendered);
                }
                OnOff.setup();
                common.setupDropdowns();
                validate();
            });
        },
        error: common.ajaxError,
    });
});
