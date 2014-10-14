define(['jquery', 'common'],
function ($, common)
{
    var ACCESS_KEY_LENGTH = 20;
    var SECRET_KEY_LENGTH = 40;

    var ACCESS_KEY_ERROR = 'Please provide a valid Access key ID.  Your Access Key ID contains 20 characters.';
    var SECRET_KEY_ERROR = 'Please provide a valid Secret Access key.  Your secret Access Key contains 40 characters.';

    var base_url = null;

    function clear() {
        $('input[type="text"], input[type="password"').val(null);
    }

    function save() {
        var data = {'action': 'save'};
        $('input[type="text"], input[type="password"]').each(function () {
            var name = $(this).attr('name');
            if (name == null) {
                name = $(this).attr('id');
                if (name == null) {
                    return;
                }
            }
            data[name] = $(this).val();
        });

        var result = null;
        $.ajax({
            type: 'POST',
            url: base_url + '/save',
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
            update(result);
        }
    }

    function cancel() {
        query(true);
        validate();
    }

    function del() {
        var success;
        $.ajax({
            type: 'POST',
            url: base_url + '/delete',
            data: {'action': 'delete'},
            dataType: 'json',
            async: false,

            success: function(data) {
                success = true;
            },
            error: function (jqXHR, textStatus, errorThrown) {
                alert(this.url + ": " +
                      jqXHR.status + " (" + errorThrown + ")");
                sucess = false;
            }
        });
        if (success) {
            clear();
            validate();
        }
    }

    function validate() {
        var enabled = true;

        var access_key = $('#access-key').val();
        if (access_key.length == ACCESS_KEY_LENGTH) {
            $('#access-key').removeClass('invalid');
            $('label[for="access-key"]').html('&nbsp;');
        } else {
            enabled = false;
            if (access_key.length > 0) {
                $('label[for="access-key"]').html(ACCESS_KEY_ERROR);
                $('#access-key').addClass('invalid');
            } else {
                $('label[for="access-key"]').html('&nbsp;');
                $('#access-key').removeClass('invalid');
            }
        }

        var secret_key = $('#secret-key').val();
        if (secret_key.length == SECRET_KEY_LENGTH) {
            $('#secret-key').removeClass('invalid');
            $('label[for="secret-key"]').html('&nbsp;');
        } else {
            enabled = false;
            if (secret_key.length > 0) {
                $('label[for="secret-key"]').html(SECRET_KEY_ERROR);
                $('#secret-key').addClass('invalid');
            } else {
                $('label[for="secret-key"]').html('&nbsp;');
                $('#secret-key').removeClass('invalid');
            }
        }

        if ($('#url').val().length < 1) {
            enabled = false;
        }

        if (enabled) {
            $('#save').removeClass('disabled');
        } else {
            $('#save').addClass('disabled');
        }
    }

    function update(data) {
        for (var key in data) {
            $('#' + key).val(data[key]);
        }
    }

    /*
     * query()
     * Send an AJAX request to the rest handler.
     */
    function query(sync) {
        if (sync == null) {
            sync = false;
        }
        $.ajax({
            url: base_url,
            sync: sync,
            success: function(data) {
                $().ready(function() {
                    update(data);
                    validate();
                });
            },
            error: common.ajaxError
        });
    }

    /*
     * setup()
     */
    function setup(url) {
        base_url = url;

        common.startMonitor(false);
        query();

        common.setupOkCancel();

        $().ready(function() {
            $('#save').bind('click', save);
            $('#cancel').bind('click', cancel);
            $('#delete').data({'callback': del});
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
    }

    return {'setup': setup};
});
