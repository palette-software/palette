define(['jquery', 'common', 'Dropdown', 'OnOff', 'lightbox'],
function ($, common, Dropdown, OnOff)
{
    var MAIL_DIRECT = 1;
    var MAIL_RELAY = 2;
    var MAIL_NONE = 3;

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
        $('#mail-test-message').html("");
        $('#mail-test-message').addClass('hidden');
        $('#mail-test-message').removeClass('green red');
    }

    /*
     * validateSection()
     * Enable/Disable the Save and Cancel buttons on particular section.
     */
    function validateSection(name, gather, maySave, mayCancel)
    {
        var data = gather(name);
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

    /*
     * gatherURLData()
     */
    function gatherURLData()
    {
        return {'server-url': $('#server-url').val()};
    }

    /*
     * gatherTableauURLData()
     */
    function gatherTableauURLData()
    {
        return {'tableau-server-url': $('#tableau-server-url').val()};
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
            'smtp-password': $('#smtp-password').val()
        };
    }

    /*
     * gatherTzData()
     * Return the current settings in the 'Timezone' section as a dict.
     */
    function gatherTzData() {
        var data = {};

        var id = 'timezone';
        data[id] = Dropdown.getValueById(id);

        return data;
    }

    /*
     * validAdminData(data)
     */
    function validAdminData(data)
    {
        var password = data['password'];
        if (password.length == 0) {
            return false;
        }
        var confirm_password = data['confirm-password'];
        if (confirm_password.length == 0) {
            return false;
        }
        if (password != confirm_password) {
            return false;
        }
        return true;
    }

    /*
     * validMailData(data)
     */
    function validMailData(data)
    {
        var type = data['mail-server-type'];
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
        if ((data['smtp-port'].length == 0) || (isNaN(data['smtp-port']))) {
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
     * setInputCallback()
     * Set a callback for whenever input is entered - likely for validation.
     */
    function setInputCallback(callback)
    {
        $('input[type="text"], input[type="password"], textarea').on('paste', function() {
            setTimeout(function() {
                /* validate after paste completes by using a timeout. */
                callback();
            }, 100);
        });
        $('input[type="text"], input[type="password"], textarea').on('keyup', function() {
            callback();
        });
    }

    return {
        'MAIL_NONE': MAIL_NONE,
        'MAIL_DIRECT': MAIL_DIRECT,
        'MAIL_RELAY': MAIL_RELAY,
        'changeMail': changeMail,
        'validateSection': validateSection,
        'gatherURLData': gatherURLData,
        'gatherTableauURLData': gatherTableauURLData,
        'gatherAdminData': gatherAdminData,
        'gatherMailData': gatherMailData,
        'gatherTzData': gatherTzData,
        'validAdminData': validAdminData,
        'validMailData': validMailData,
        'setInputCallback': setInputCallback,
    }
});
