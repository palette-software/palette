require(['jquery', 'common', 'form', 'template', 'Dropdown'],
function ($, common, form, template, Dropdown)
{
    var URL = '/rest/support-case';
    var NONE = '--None--'

    var templates;

    /*
     * jq()
     * Escape selector characters in 'id'.
     * see: learn.jquery.com -> jq().
     */
    function jq(id) {
        return "#" + id.replace( /(:|\.|\[|\]|,)/g, "\\$1" );
    }

    /*
     * cookieName()
     * cookies can't contain semicolons...
     */
    function cookieName(id) {
        return id.replace(':', '.');
    }

    /*
     * gather()
     * Collect all of the form information.
     */
    function gather() {
        var data = {}

        /* text inputs */
        $('input[type=text], textarea').each(function(index) {
            var id = $(this).attr('id');
            data[id] = $(jq(id)).val();
        });

        $('input[type=checkbox]').each(function(index) {
            var id = $(this).attr('id');
            data[id] = this.checked;
        });

        /* dropdowns */
        $('.btn-group').each(function(index){
            var id = $(this).attr('id');
            data[id] = Dropdown.getValueByNode(this);
        });
        return data;
    }

    /*
     * cache()
     * Save fields marked with the 'cache' class to cookies.
     * NOTE: should be called after validate().
     */
    function cache() {
        $('input[type=text].cache, textarea.cache').each(function(index){
            var id = $(this).attr('id');
            var value = $(jq(id)).val();
            if (value != null && value.length > 0) {
                common.setCookie(cookieName(id), value);
            } else {
                common.deleteCookie(cookieName(id));
            }
        });

        /* dropdowns */
        $('.btn-group.cache').each(function(index){
            var id = $(this).attr('id');
            var value = Dropdown.getValueByNode(this);
            if (value != null && value.length > 0) {
                common.setCookie(cookieName(id), value);
            } else {
                common.deleteCookie(cookieName(id));
            }
        });
    }

    /*
     * fgError()
     */
    function fgError($fg, msg) {
        $fg.addClass('has-error');
        $fg.append(form.fieldError(msg));
    }


    /*
     * validate()
     */
    function validate(button) {
        form.clearErrors();

        var result = true;
        $('input[type=text], textarea').each(function(index){
            var $fg = $(this).parent();
            var value = $(this).val().trim();
            var required = $fg.hasClass('required');

            if (required && value.length == 0) {
                fgError($fg, 'This field is required.');
                result = false;
                return;
            }

            if ($(this).hasClass('url')) {
                if (value.length > 0) {
                    if (!form.validURL(value)) {
                        fgError($fg, 'Please specify a valid URL.');
                        result = false;
                    }
                }
            } else if ($(this).hasClass('phone')) {
                if (value.length > 0) {
                    if (!form.validPhoneNumber(value)) {
                        fgError($fg, 'Please specify a valid phone number.');
                        result = false;
                    }
                }
            } else if ($(this).hasClass('email')) {
                if (value.length > 0) {
                    if (!form.validEmail(value)) {
                        fgError($fg, 'Please specify a valid email address.');
                        result = false;
                    }
                }
            }
        });

        /* dropdowns */
        $('.btn-group').each(function(index){
            var $fg = $(this).parent();
            if ($fg.hasClass('required')) {
                if (Dropdown.getValueByNode(this) == NONE) {
                    fgError($fg, 'This field is required.');
                    result = false;
                }
            }
        });

        if (!result) {
            var msg = "The page contains invalid input, please correct."

            var html = form.pageError(msg);
            $(".top-zone").append(html);
            $(".save-cancel").prepend(html);
            $(".dynamic-content .scrollable").scrollTop(0);
        }

        return result;
    }

    /*
     * sendSupportCase()
     */
    function sendSupportCase() {
        $('#send-support-case').addClass('disabled');
        form.clearErrors();
        cache();

        $.ajax({
            type: 'POST',
            url: URL,
            data: gather(),
            dataType: 'json',
            
            success: function(data) {
                var rendered = template.render(templates['thank-you']);
                $('.bottom-zone').html(rendered);

                $('#send-support-case').removeClass('disabled');
                $('#okcancel').removeClass('visible');
            },
            error: function(jqXHR, textStatus, errorThrown) {
                common.ajaxError(jqXHR, textStatus, errorThrown);
                $('#send-support-case').removeClass('disabled');
                $('#okcancel').removeClass('visible');
            }
        });
    }

    /*
     * update()
     */
    function update(data) {
        $('input[type=text]').each(function(index){
            var id = $(this).attr('id');
            if (id == null) {
                return;
            }
            var value = data[id];
            if (value != null) {
                $(jq(id)).val(value);
            } else {
                value = common.getCookie(cookieName(id));
                if (value != null) {
                    value = value.replace('_', ' ');
                    $(jq(id)).val(value);
                }
            }
        });

        Dropdown.setupAll(data);
        
        /* dropdowns */
        $('.btn-group.cache').each(function(index){
            var value = Dropdown.getValueByNode(this);
            if (value == NONE) {
                var cookie = common.getCookie(cookieName($(this).attr('id')));
                if (cookie != null && cookie.length > 0) {
                    cookie = cookie.replace('_', ' ');
                    Dropdown.setValueByNode(this, cookie);
                }
            }
        });
    }

    common.startMonitor(false);
    common.setupOkCancel();

    $.ajax({
        url: URL,
        dataType: 'json',
        
        success: function(data) {
            $().ready(function() {
                templates = common.loadTemplates();
                update(data);
                $('#send-support-case').data('validate', validate);
                $('#send-support-case').data('callback', sendSupportCase);
                $('#send-support-case').removeClass('disabled');
            });
        },
        error: common.ajaxError,
    });
});
