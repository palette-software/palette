require(['jquery', 'configure', 'common', 'form', 'template',
         'Dropdown', 'OnOff',
         'bootstrap'],
function ($, configure, common, form, template, Dropdown, OnOff)
{
    var setupDone = false;

    /* Determines whether or not the mail configuration settings are present
       on the initial setup page e.g. hidden for Pro */
    var hasSettings = {'mail': true,
                       'server-url': true,
                       'license-key': true}

    var LICENSING_TIMEOUT = 3000; // 3 sec;

    var LICENSING_UNKNOWN = -1;
    var LICENSING_FAILED = 0;
    var LICENSING_OK = 1;

    var licensingState = LICENSING_UNKNOWN;
    var licensingTimeout = null;
    var licensingStatusTimeout = null;

    var PASSWORD_MIN_CHARS = 8;
    var PASSWORD_MATCH = /^[A-Za-z0-9!@#$%]+$/;

    var templates;

    /*
     * setPageError()
     * Set the main error reporting at the top and bottom of the page.
     */
    function setPageError(msg)
    {
        var html = form.pageError(msg);
        $(".top-zone").append(html);
        $("#save").before(html);
    }

    /*
     * setError()
     * Add an error message after the element specified by the selector.
     * Usually the selected element will be an input field.
     */
    function setError(selector, msg)
    {
        var html = form.fieldError(msg)
        $(selector).parent().addClass('has-error');
        $(selector).after(html);
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
        $.extend(data, configure.gatherTzData());
        return data;
    }

    /*
     * save_callback()
     * Callback when the save AJAX call was successfully sent to the server.
     * NOTE: the *data* may still have an error.
     */
    function save_callback(data) {
        if (data['status'] == 'OK') {
            window.location.replace("/");
            return;
        }

        var error = data['error'] || 'Unknown server error';
        setPageError(error);
    }

    /*
     * connect()
     * Callback for the 'connect' button during 'Failed to Contact Licensing'.
     */
    function connect() {
        form.clearErrors();

        var data = {'action': 'proxy'}

        var proxy_https = $('#proxy-https').val();
        if (proxy_https.length == 0) {
            /* Include 'value' but set it to null to indicate the key
             * proxy-https should be deleted from the system table (hack).
             * FIXME: use 'DELETE' instead.
             */
            data['value'] = null;
        } else {
            if (!form.validURL(proxy_https)) {
                // put the error at the end of the proxy div
                setError('#connect', 'The URL is invalid.');
                return;
            }
            data['value'] = proxy_https;
        }

        clearTimeout(licensingTimeout);
        $('#connect').addClass('disabled');

        $.ajax({
            type: 'POST',
            url: '/open/setup', /* should be /open/setup/proxy */
            data: data,
            dataType: 'json',

            success: function(data) {
                licensingQuery();
            },
            error: function (jqXHR, textStatus, errorThrown) {
                alert(this.url + ": " +
                      jqXHR.status + " (" + errorThrown + ")");
                licensingQuery(); /* just in case... */
            }
        });
    }

    /*
     * save()
     * Callback for the 'Save' button.
     */
    function save() {
        form.clearErrors();

        var data = {'action': 'save'}
        $.extend(data, gatherData());

        if (!validateForSave(data)) {
            setPageError("The page contains invalid input, please correct.");
            $("body").scrollTop(0);
            return;
        }

        $.ajax({
            type: 'POST',
            url: '/open/setup',
            data: data,
            dataType: 'json',

            success: save_callback,
            error: function (jqXHR, textStatus, errorThrown) {
                var msg = this.url + ": " + jqXHR.status + " (" + errorThrown + ")";
                setPageError(msg);
            }
        });
    }

    /*
     * testMail()
     * Callback for the 'Test Email' button.
     */
    function testMail() {
        form.clearErrors();
        $('#mail-test-message').html("");
        $('#mail-test-message').addClass('hidden');
        $('#mail-test-message').removeClass('green red');

        var data = {'action': 'test'}
        $.extend(data, configure.gatherMailData());
        data['test-email-recipient'] = $('#test-email-recipient').val();

        if (!validateForTest(data)) {
            return;
        }

        var result = {};
        $.ajax({
            type: 'POST',
            url: '/open/setup',  /* fixme - maybe /open/setup/mail? */
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
     * validatePasswordChars()
     * Ensure that the password contains on valid characters
     */
    function validatePasswordChars(pw) {
        return pw.match(PASSWORD_MATCH);
    }

    /*
     * validateAdminData(data)
     * FIXME: merge with configure.
     */
    function validateAdminData(data)
    {
        var result = true;

        var password = data['password'];
        if (password.length == 0) {
            setError("#password", "Password is required.");
            result = false;
        } else if (password.length < PASSWORD_MIN_CHARS) {
            var msg = "The password must contain at least " + PASSWORD_MIN_CHARS + " characters.";
            setError("#password", msg);
            result = false;
        } else if (!validatePasswordChars(password)) {
            setError("#password", "The password contains invalid characters.");
            result = false;
        }
            
        var confirm_password = data['confirm-password'];
        if (confirm_password.length == 0) {
            setError("#confirm-password", "Confirmation password is required.");
            result = false;
        }
        if (result && (password != confirm_password)) {
            setError("#password", "Passwords must match.");
            result = false;
        }
        return result;
    }

    /*
     * validateMailData(data)
     */
    function validateMailData(data)
    {
        var result = true;

        var type = data['mail-server-type'];
        if (type == configure.MAIL_NONE) {
            /* Getting here implies mail server type changed. */
            return true;
        }

        if (!form.validEmail(data['alert-email-address'])) {
            setError("#alert-email-address", "The email address is invalid.");
            result = false;
        }

        if (type == configure.MAIL_DIRECT) {
            return result;
        }

        if (data['smtp-server'].length == 0) {
            setError("#smtp-server", "The mail server is required.");
            result = false;
        }

        var port = data['smtp-port'];
        if (port == null || port == 0) {
            setError("#smtp-port", "The port is required.");
            result = false;
        } else if (isNaN(port)) {
            setError("#smtp-port", "The port is invalid.");
            result = false;
        }

        /* SMTP username and password are optional */
        if (data['smtp-username'].length > 0
            && data['smtp-password'].length == 0) {
            setError("#smtp-password",
                     "The password is required when a username is specified.");
            result = false;
        } else if (data['smtp-username'].length == 0
                   && data['smtp-password'].length > 0) {
            setError("#smtp-username",
                     "The username is required when a password is specified.");
            result = false;
        }

        return result;
    }

    /*
     * validateForSave()
     * Test all input when the user presses the save button.
     */
    function validateForSave(data) {
        var result = true;

        if (!setupDone) {
            result = false;
        }

        if (hasSettings['server-url']) {
            if (!form.validURL(data['server-url'])) {
                setError("#server-url", "Invalid URL");
                result = false;
            }
        }
        if (!form.validURL(data['tableau-server-url'])) {
            setError("#tableau-server-url", "Invalid URL");
            result = false;
        }
        if (hasSettings['license-key']) {
            if (data['license-key'].length < 2) { // FIXME //
                setError("#license-key", "Invalid license key");
                result = false;
            }
        }
        if (!validateAdminData(data)) {
            result = false;
        }
        if (hasSettings['mail']) {
            if (!validateMailData(data)) {
                result = false;
            }
        }
        return result;
    }

    /*
     * validateForTest()
     * Validate the email setting when the user presses the test button.
     */
    function validateForTest(data) {
        var result = validateMailData(data);
        if (!form.validEmail(data['test-email-recipient'])) {
            /* put the error after the button */
            setError("#test-mail","Invalid email address");
            result = false;
        }
        return result;
    }

    function setup(data)
    {
        if ($('#server-url').length == 0) {
            hasSettings['server-url'] = false;
        }
        if ($('#license-key').length == 0) {
            hasSettings['license-key'] = false;
        }
        if ($('#mail-server-type').length == 0) {
            hasSettings['mail'] = false;
        }

        Dropdown.setupAll(data);
        OnOff.setup();

        $('#proxy-https').val(data['proxy-https']);
        $('#save').bind('click', save);

        if (hasSettings['mail']) {
            $('#test-mail').bind('click', testMail);
            $('#test-mail').removeClass('disabled'); /* FIXME */
        }

        if (hasSettings['server-url']) {
            $('#server-url').val(data['server-url']);
        }
        $('#tableau-server-url').val(data['tableau-server-url']);
        if (hasSettings['license-key']) {
            $('#license-key').val(data['license-key']);
        }

        if (hasSettings['mail']) {
            $('#alert-email-name').val(data['alert-email-name']);
            $('#alert-email-address').val(data['alert-email-address']);

            $('#smtp-server').val(data['smtp-server']);
            $('#smtp-port').val(data['smtp-port']);
            $('#smtp-username').val(data['smtp-username']);
            $('#smtp-password').val(data['smtp-password']);

            /* layout changes based on selections */
            Dropdown.setCallback(function () {
                configure.changeMail();
            }, '#mail-server-type');
            configure.changeMail();
        }

        /* help */
        common.lightbox(236535, 'Palette Server URL');
        common.lightbox(237794, 'Tableau Server URL');
        common.lightbox(237795, 'License Key');
        common.lightbox(236536, 'Palette Admin Password');
        common.lightbox(252063, 'Tableau Server Repository Database User Password');
        common.lightbox(236542, 'Mail Server');
        common.lightbox(236544, 'Authentication');
        common.lightbox(237785, 'Timezone');

        $(".version").html(data['version']);

        setupDone = true;
    }

    /*
     * displayTemplate()
     * Show the content of a template in the main container.
     */
    function displayTemplate(tmpl)
    {
        /* don't display the 'prepare for awesomeness' message */
        $("body .container > div").not('.top-zone, .bottom-zone').remove();

        var rendered = template.render(templates[tmpl]);
        $("body .container").prepend(rendered);
        $("#connect").removeClass("disabled");
    }

    /*
     * licensingQuery()
     */
    function licensingQuery()
    {
        $.ajax({
            url: '/licensing',
            success: function(data) {
                $().ready(function() {
                    licensingState = LICENSING_OK;
                    $("body .container > div").not('.top-zone, .bottom-zone').remove();
                    $(".top-zone, .bottom-zone").removeClass('hidden');
                });
            },
            error: function (jqXHR, textStatus, errorThrown) {
                $().ready(function() {
                    if (licensingState != LICENSING_FAILED) {
                        var tmpl = templates['licensing-error'];
                        displayTemplate('licensing-error');
                        licensingState = LICENSING_FAILED;
                    }
                    /* try again ... */
                    licensingTimeout = setTimeout(licensingQuery,
                                                  LICENSING_TIMEOUT);
                });
            }
        });
    }

    /* Ensure that the server can talk to licensing. */
    licensingQuery();
    $().ready(function() {
        templates = common.loadTemplates();
        page = $("body > div").html();
        /* Display a status message after half a second if the
           licensing query is not already complete. */
        licensingStatusTimeout = setTimeout(function () {
            if (licensingState == LICENSING_UNKNOWN) {
                displayTemplate('licensing-status');
            }
        }, 500); /* half second? */

        $('#connect').bind('click', connect);
    });

    /* fill in initial values */
    $.ajax({
        url: '/open/setup',
        success: function(data) {
            $().ready(function() {
                setup(data);
            });
        },
        error: function (jqXHR, textStatus, errorThrown) {
            setPageError("Your browser is disconnected.");
        }
    });
});
