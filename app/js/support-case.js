require(['jquery', 'common', 'form', 'Dropdown'],
function ($, common, form, Dropdown)
{
    var URL = '/rest/support-case';
    var NONE = '--None--'

    /*
     * jq()
     * Escape selector characters in 'id'.
     * see: learn.jquery.com -> jq().
     */
    function jq(id) {
        return "#" + id.replace( /(:|\.|\[|\]|,)/g, "\\$1" );
    }

    /*
     * gather()
     * Collect all of the form information.
     */
    function gather() {
        var data = {}

        /* inputs */
        $('input[type=text], textarea').each(function(index){
            var id = $(this).attr('id');
            data[id] = $(jq(id)).val();
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
                common.setCookie(id, value);
            } else {
                common.deleteCookie(id);
            }
        });

        /* dropdowns */
        $('.btn-group.cache').each(function(index){
            var id = $(this).attr('id');
            var value = Dropdown.getValueByNode(this);
            if (value != null && value.length > 0) {
                common.setCookie(id, value);
            } else {
                common.deleteCookie(id);
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
    function validate() {
        var result = true;
        $('input[type=text], textarea').each(function(index){
            var $fg = $(this).parent();
            var value = $(this).val().trim();
            var required = $fg.hasClass('required');

            if (required && value.length == 0) {
                fgError($fg, 'This field is required.');
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
        return result;
    }

    /*
     * clearErrors()
     */
    function clearErrors() {
        $('.has-error').removeClass('has-error');
        $('.field-error').remove();
    }

    /*
     * sendSupportCase()
     */
    function sendSupportCase() {
        $('#send-support-case').addClass('disabled');
        clearErrors();

        if (!validate()) {
            $('#send-support-case').removeClass('disabled');
            return;
        }
        cache();

        $.ajax({
            type: 'POST',
            url: URL,
            data: gather(),
            dataType: 'json',
            
            success: function(data) {
                $('#send-support-case').removeClass('disabled');
                $('#okcancel').removeClass('visible');
            },
            error: function(jqXHR, textStatus, errorThrown) {
                common.ajaxError(jqXHR, textStatus, errorThrown);
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
                value = common.getCookie(id);
                if (value != null) {
                    $(jq(id)).val(value);
                }
            }
        });

        Dropdown.setupAll(data);
        
        /* dropdowns */
        $('.btn-group.cache').each(function(index){
            var id = $(this).attr('id');
            var value = Dropdown.getValueByNode(this);
            if (value == NONE) {
                var cookie = common.getCookie(id);
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
                update(data);
                $('#send-support-case').data('callback', sendSupportCase);
                $('#send-support-case').removeClass('disabled');
            });
        },
        error: common.ajaxError,
    });
});
