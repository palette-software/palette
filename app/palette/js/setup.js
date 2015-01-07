require(['jquery', 'template', 'common', 'OnOff', 'bootstrap'],
function ($, template, common, OnOff)
{    
    /*
     * clear()
     * Empty all input fields.
     */
    function clear() {
        $('input[type="text"], input[type="password"').val(null);
    }

    /*
     * save()
     * Callback for the 'Save' button.
     */
    function save() {
        var fields = ['password',
                      'alert-email-name', 'alert-email-address',
                      'smtp-server', 'smtp-port',
                      'smtp-username', 'smtp-password']

        var data = {'action': 'save'}
        for (var index = 0; index < fields.length; index++) {
            data[fields[index]] = $('#' + fields[index]).val();
        };
        data['mail-server-type'] = $('#mail-server-type > button > div').attr('data-id');
        data['enable-tls'] = $('#enable-tls .onoffswitch-checkbox').prop("checked");

        var result = null;
        $.ajax({
            type: 'POST',
            url: '/rest/setup',
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
            window.location.replace("/");
        }
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
        var password = $('#password').val();
        if (password.length == 0) {
            return false;
        }
        var confirm_password = $('#confirm-password').val();
        if (confirm_password.length == 0) {
            return false;
        }
        if (password != confirm_password) {
            return false;
        }
        return true;
    }

    /*
     * test_valid()
     * Test input and return true/false.
     */
    function test_valid() {
        var recipient = $('#test-email-recipient').val();
        if (recipient.length < 3) {
            return false;
        }
        if (recipient.indexOf('@') == -1) {
            return false;
        }
        return true;
    }

    /*
     * validate()
     * Enable/disable the 'Save' button based on the field values.
     */
    function validate() {
        var save_enabled = save_valid();
        if (save_enabled) {
            $('#save').removeClass('disabled');
        } else {
            $('#save').addClass('disabled');
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
        $('#save').bind('click', save);
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
            });
        },
        error: common.ajaxError,
    });
});
