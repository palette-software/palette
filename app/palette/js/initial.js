require(['jquery', 'configure', 'common', 'Dropdown', 'OnOff', 'bootstrap'],
function ($, configure, common, Dropdown, OnOff)
{
    var LICENSE_TIMEOUT = 1000; // 1 sec;

    /*
     * inputValid()
     * Return whether or not an input field has been filed in (at all) by id.
     */
    function inputValid(id) {
        return ($('#'+id).val().length > 0);
    }

    /*
     * gatherData()
     */
    function gatherData() {
        var data = {};
        data['license-key'] = $('#license-key').val();
        $.extend(data, configure.gatherURLData());
        $.extend(data, configure.gatherAdminData());
        $.extend(data, configure.gatherMailData());
        $.extend(data, configure.gatherSSLData());
        return data;
    }

    /*
     * save()
     * Callback for the 'Save' button.
     */
    function save() {
        var data = {'action': 'save'}
        $.extend(data, gatherData());

        var result = null;
        $.ajax({
            type: 'POST',
            url: '/open/setup',
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
            url: '/open/setup/email',
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
            /* FIXME */
            alert('OK');
        }
    }


    /*
     * maySave()
     * Test input and return true/false.
     */
    function maySave(data) {
        if (!common.validURL(data['server-url'])) {
            return false;
        }
        if (data['license-key'].length < 2) { // FIXME //
            return false;
        }
        if (!configure.validAdminData(data)) {
            return false;
        }
        if (!configure.validMailData(data)) {
            return false;
        }
        if (!configure.validSSLData(data)) {
            return false;
        }
        return true;
    }

    /*
     * mayTest()
     * Test input and return true/false.
     */
    function mayTest() {
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
        var data = gatherData();
        if (maySave(data)) {
            $('#save').removeClass('disabled');
        } else {
            $('#save').addClass('disabled');
        }

        if (mayTest()) {
            $('#test').removeClass('disabled');
        } else {
            $('#test').addClass('disabled');
        }
    }

    function setup(data)
    {
        Dropdown.setupAll(data);
        OnOff.setup();

        $('#save').bind('click', save);
        $('#test').bind('click', test);

        $('#server-url').val(data['server-url']);

        /* validation */
        Dropdown.setCallback(validate);
        Dropdown.setCallback(function () {
            configure.changeMail();
            validate();
        }, '#mail-server-type');
        configure.changeMail();
        /* this assumes no other OnOff sliders on the initial setup page. */
        OnOff.setCallback(function (checked) {
            configure.changeSSL(checked);
            validate();
        }, '#enable-ssl');
        configure.setInputCallback(validate);
        /* no need to call validate(), the form can't be valid yet. */
    }

    /*
     * queryLicensing()
     */
    function queryLicensing()
    {
        $.ajax({
            url: '/licensing',
            success: function(data) {
                $('div.error-page').addClass('hidden');
                $('div.setup-page').removeClass('hidden');
            },
            error: function (jqXHR, textStatus, errorThrown) {
                $('div.setup-page').addClass('hidden');
                $('div.error-page').removeClass('hidden');
                setTimeout(queryLicensing, LICENSE_TIMEOUT);
            }
        });
    }

    /* start */
    queryLicensing();

    $.ajax({
        url: '/open/setup',
        success: function(data) {
            $().ready(function() {
                setup(data);
            });
        },
        error: common.ajaxError,
    });
});
