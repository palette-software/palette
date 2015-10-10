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
     * fieldError() {
     * Add an error message to a form-group.
     */
    function fieldError(msg) {
        return '<p class="field-error">' + msg + '</p>';
    }

    return {'validEmail' : validEmail,
            'validURL' : validURL,
            'validPassword' : validPassword,
            'validPhoneNumber': validPhoneNumber,
            'fieldError': fieldError
           };
});
