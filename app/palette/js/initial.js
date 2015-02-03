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
        $.extend(data, configure.gatherTableauURLData());
        $.extend(data, configure.gatherAdminData());
        $.extend(data, configure.gatherMailData());
        $.extend(data, configure.gatherSSLData());
        $.extend(data, configure.gatherTzData());
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
            }
        });
        if (result != null) {
            window.location.replace("/");
        }
    }

    /*
     * testMail()
     * Callback for the 'Test Email' button.
     */
    function testMail() {
        var data = {'action': 'test'}
        $.extend(data, configure.gatherMailData());

        var result = {};
        $.ajax({
            type: 'POST',
            url: '/open/setup/mail',
            data: data,
            dataType: 'json',
            async: false,

            success: function() {
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
        if (!common.validURL(data['tableau-server-url'])) {
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
    function mayTest(data) {
        var recipient = $('#test-email-recipient').val();
        if (!common.validEmail(recipient)) {
            return false;
        }
        return configure.validMailData(data);
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

        if (mayTest(data)) {
            $('#test-mail').removeClass('disabled');
        } else {
            $('#test-mail').addClass('disabled');
        }
    }

    function setup(data)
    {
        Dropdown.setupAll(data);
        OnOff.setup();

        $('#save').bind('click', save);
        $('#test').bind('click', testMail);

        $('#server-url').val(data['server-url']);
        $('#tableau-server-url').val(data['server-url']);

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

        /* help */
        // FIXME: e.g.
        // configure.lightbox(id, title);

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
