require(['jquery', 'common'],
function ($, common)
{
    var ACCESS_KEY_LENGTH = 20;
    var SECRET_KEY_LENGTH = 40;
    var HIDDEN_SECRET = '****************************************';

    /* ignore 'name' for now. */
    var state = {'access-key': null, 'secret-key': null, 'bucket': null};

    function secret_key_display() {
        var value = state['secret-key'];
        if (value == null || value.length == 0) {
            value = null;
        } else {
            value = HIDDEN_SECRET;
        }
        return value;
    }

    function input_text_tag(id, value) {
        var html = '<input type="text" id="' + id + '" ';
        if (value != null && value.length > 0) {
            html += 'value="' + value + '" ';
        }
        return html + ' />';
    }

    function toggle_input_text(name) {
        var html = input_text_tag(name, state[name]);
        $('#' + name).replaceWith(html);
    }

    function toggle_p(name, value) {
        var html = '<p id="' + name + '">';
        if (value != null && value.length > 0) {
            html += value;
        }
        html += '</p>';
        $('#' + name).replaceWith(html);
    }

    function toggle() {
        toggle_p('access-key', state['access-key']);
        toggle_p('secret-key', secret_key_display());
        toggle_p('bucket', state['bucket']);
    }

    function save() {
        var data = {};
        for (var key in state) {
            data[key] = $('#' + key).val();
        }

        var success;
        $.ajax({
            type: 'POST',
            url: '/rest/s3',
            data: data,
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
            update(data);
            toggle();
            $('#save, #cancel').addClass('hidden');
            $('#edit').removeClass('hidden');
        }
    }

    function cancel() {
        toggle();
        $('#save, #cancel').addClass('hidden');
        $('#edit').removeClass('hidden');
    }

    function edit() {
        toggle_input_text('access-key');
        toggle_input_text('secret-key');
        toggle_input_text('bucket');
        $('input[type="text"]').bind("input propertychange", validate);
        $('#edit').addClass('hidden');
        $('#save, #cancel').removeClass('hidden');
        validate();
    }

    function validate() {
        var disable = false;
        if ($('#access-key').val().length != ACCESS_KEY_LENGTH) {
            $('#save').addClass('disabled');
            return;
        }
        if ($('#secret-key').val().length != SECRET_KEY_LENGTH) {
            $('#save').addClass('disabled');
            return;
        }
        if ($('#bucket').val().length < 1) {
            $('#save').addClass('disabled');
            return;
        }
        $('#save').removeClass('disabled');
    }

    function update(data) {
        if (data['secret-key'] == null) {
            data['secret-key'] = data['secret']; /* hack */
        }
        for (var key in state) {
            var value = data[key]
            state[key] = value;
        }
    }

    /*
     * query()
     * Send an AJAX request to the rest handler.
     */
    function query() {
        $.ajax({
            url: '/rest/s3',
            success: function(data) {
                $().ready(function() {
                    update(data);
                    $('#access-key').html(state['access-key']);
                    $('#secret-key').html(secret_key_display());
                    $('#bucket').html(state['bucket']);
                });
            },
            error: common.ajaxError
        });
    }

    common.startMonitor(false);
    query();

    $().ready(function() {
        $('#save').bind('click', save);
        $('#cancel').bind('click', cancel);
        $('#edit').bind('click', edit);
    });
});
