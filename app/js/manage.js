require(['jquery', 'topic', 'common', 'bootstrap'],
function ($, topic, common)
{
    var actions = {'start': start,
                   'stop': stop,
                   'backup': backup,
                   'restart': restart,
                   'repair-license': repair_license,
                   'ziplogs': ziplogs,
                  };

    var allowed = [];
    var connected;

    /*
     * disableAll()
     */
    function disableAll() {
        $('.actions a').addClass('inactive');
        return true;
    }

    function start() {
        disableAll();
        $.ajax({
            type: 'POST',
            url: '/rest/manage',
            data: {'action': 'start'},
            dataType: 'json',
            
            success: function(data) {},
            error: common.ajaxError,
        });
    }

    function stop() {
        disableAll();
        data = {'action': 'stop'}
        $('#popupStop input[type=checkbox]').each(
            function(index, item){
                data[item.name] = item.checked;
            }
        );
        $.ajax({
            type: 'POST',
            url: '/rest/manage',
            data: data,
            dataType: 'json',

            success: function(data) {
                /* reset the defaults in the popup dialog */
                $('#popupStop input[type=checkbox]').prop('checked', true);
            },
            error: common.ajaxError,
        });
    }

    function restart() {
        disableAll();
        data = {'action': 'restart'}
        $('#popupRestart input[type=checkbox]').each(
            function(index, item){
                data[item.name] = item.checked;
            }
        );
        $.ajax({
            type: 'POST',
            url: '/rest/manage',
            data: data,
            dataType: 'json',

            success: function(data) {
                /* reset the default values in the dialog. */
                $('#popupRestart input[type=checkbox]').prop('checked', true);
            },
            error: common.ajaxError,
        });
    }

    function ziplogs() {
        disableAll();
        $.ajax({
            type: 'POST',
            url: '/rest/manage',
            data: {'action': 'ziplogs'},
            dataType: 'json',

            success: function(data) {},
            error: common.ajaxError,
        });
    }

    function backup() {
        disableAll();
        $.ajax({
            type: 'POST',
            url: '/rest/backup',
            data: {'action': 'backup'},
            dataType: 'json',
            
            success: function(data) {},
            error: common.ajaxError,
        });
    }

    function repair_license() {
        disableAll();
        $.ajax({
            type: 'POST',
            url: '/rest/manage',
            data: {'action': 'repair-license'},
            dataType: 'json',
            
            success: function(data) {
                updateActions();
            },
            error: common.ajaxError,
        });
    }

    /*
     * showRestore()
     * show action for the restore popup - sets up the dialog text.
     */
    function showRestore(modal) {
        var timestamp = $('span.timestamp', this.$element[0]).text();
        var filename = $('span.filename', this.$element[0]).text();
        $('#restore-timestamp').html(timestamp);
        $('#restore-filename').val(filename);
        return true;
    }

    /*
     * restore()
     * confirm action
     */
    function restore() {
        var data = {'action': 'restore',
                    'filename': $('#restore-filename').val()};
        $('#restore-dialog input[type=checkbox]').each(
            function(index, item){
                data[item.name] = item.checked;
            }
        );

        var passwd = $('#password').val();
        if (passwd != null && passwd.length > 0) {
            data['password'] = passwd;
        }
        $('#password').val('');

        data['restore-type'] = $('#restore-dialog input[type=radio]:checked').val();

        $.ajax({
            type: 'POST',
            url: '/rest/backup',
            data: data,
            dataType: 'json',
            
            success: function(data) {
                $('#restore-dialog input[type=checkbox]').prop('checked', true);
            },
            error: common.ajaxError,
        });
    }

    /*
     * updateActions()
     * Enable/Disable actions based on the 'allowed' list.
     */
    function updateActions() {
        for (var action in actions) {
            if ($.inArray(action, allowed) >= 0) {
                $('#'+action).removeClass('inactive');
            } else {
                $('#'+action).addClass('inactive');
            }
        }
    }

    /*
     * updateState()
     */
    function updateState() {
        updateActions();
        updateBackups();
    }

    function updateBackupSuccess(data) {
        $('#backup-list').render('backup-list-template', data);

        $('li.backup a').data('show', showRestore);
        $('li.backup a').data('confirm', restore);

        if ($.inArray('restore', allowed) >= 0) {
            $('li.backup a').removeClass('inactive');
        }

        $('#next-backup').html(data['next']);
    }

    function updateBackups() {
        if (connected) {
            $.ajax({
                url: '/rest/backup',
                success: function(data) {
                    $().ready(function() {
                        updateBackupSuccess(data);
                    });
                },
                error: common.ajaxError,
            });
        }
    }

    /* setup */
    topic.subscribe('state', function(message, data) {
        allowed = data['allowable-actions'];
        connected = data['connected'];
        updateState();
    });
    common.startMonitor();

    $().ready(function() {
        $(".content").addClass("with-secondary-sidebar");
        /* bind basic actions */
        for (var key in actions) {
            $('#'+key).data('confirm', actions[key]);
        }
    });
});
