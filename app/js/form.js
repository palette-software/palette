define(['jquery'],
function ($)
{
    /*
     * Test if the value is a valid email address or not.
     */
    function validEmail(email) {
        var regex = /^([a-zA-Z0-9_.+-])+\@(([a-zA-Z0-9-])+\.)+([a-zA-Z0-9]{2,4})+$/;
        return regex.test(email);
    }

    /*
     * Test if the value is a valid URL or not.
     */
    function validURL(url) {
        // var regex = /^(([a-zA-Z0-9-\.])+\.)([a-zA-Z0-9]{2,4})+$/;
        var regex = /^http:\/\/\S+$|^https:\/\/\S+$/;
        return regex.test(url.toLowerCase());
    }

    /*
     * Test if the value is a valid password or not.
     */
    function validPassword(value) {
        var regex = /^([a-zA-Z0-9-!@#$%^&]){8,}$/;
        return regex.test(value);
    }

    /*
     * Test if a valid phone number or not.
     * http://www.w3resource.com/javascript/form/phone-no-validation.php
     */
    function validPhoneNumber(value)
    {
        var regex = /^\(?([0-9]{3})\)?[-. ]?([0-9]{3})[-. ]?([0-9]{4})$/;
        return regex.test(value);
    }

    /*
     * fieldError()
     * Create an error message for a particular field.
     */
    function fieldError(msg) {
        return '<p class="field-error">' + msg + '</p>';
    }

    /*
     * pageError()
     * Create a page error message.
     */
    function pageError(msg)
    {
        return '<h3 class="page-error">' + msg + '</h3>';
    }

    /*
     * clearErrors()
     * Remove all created error elements.
     */
    function clearErrors()
    {
        $('.has-error').removeClass('has-error');
        $('.page-error, .field-error').remove();
    }

    return {'validEmail' : validEmail,
            'validURL' : validURL,
            'validPassword' : validPassword,
            'validPhoneNumber': validPhoneNumber,
            'fieldError': fieldError,
            'pageError': pageError,
            'clearErrors': clearErrors
           };
});
