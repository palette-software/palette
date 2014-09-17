require(['jquery', 'topic', 'template', 'common', 'bootstrap'],
function ($, topic, template, common)
{
    var actions = {'start': start,
                   'stop': stop,
                   'backup': backup,
                   'restart': ok,
                   'repair-license': ok,
                   'ziplogs': ziplogs,
                  };

    var templates = {'backup-list-template': null,
                     'archive-backup-template': null};

    var allowed = [];

    function disableAll() {
        /* FIXME - do this with a class */
        for (var action in actions) {
            $('#'+action).addClass('inactive');
        }
    }

    /*
     * ok()
     * Generic 'OK' handler for placeholder actions.
     */
    function ok() {
        updateState();
    }

    function start() {
        $.ajax({
            type: 'POST',
            url: '/rest/manage',
            data: {'action': 'start'},
            dataType: 'json',
            async: false,
            
            success: function(data) {},
            error: common.ajaxError,
        });
    }

    function stop() {
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
            async: false,

            success: function(data) {},
            error: common.ajaxError,
        });
    }

    function ziplogs() {
        $.ajax({
            type: 'POST',
            url: '/rest/manage',
            data: {'action': 'ziplogs'},
            dataType: 'json',
            async: false,

            success: function(data) {},
            error: common.ajaxError,
        });
    }

    function backup() {
        $.ajax({
            type: 'POST',
            url: '/rest/backup',
            data: {'action': 'backup'},
            dataType: 'json',
            async: false,
            
            success: function(data) {},
            error: common.ajaxError,
        });
    }

    function restore() {
        var ts = $('#restore-timestamp').html();
        var filename = $('#restore-filename').val();

        $.ajax({
            type: 'POST',
            url: '/rest/backup',
            data: {'action': 'restore',
                   'filename': filename},
            dataType: 'json',
            async: false,
            
            success: function(data) {},
            error: common.ajaxError,
        });
    }

    /*
     * updateState()
     * Enable/Disable actions based on the 'allowed' list.
     */
    function updateState() {
        for (var action in actions) {
            if ($.inArray(action, allowed) >= 0) {
                $('#'+action).removeClass('inactive');
            } else {
                $('#'+action).addClass('inactive');
            }
        }

        updateBackups();
    }

    function updateBackupSuccess(data) {
        var t = templates['backup-list-template'];
        var rendered = template.render(t, data);
        $('#backup-list').html(rendered);

        var config = data['config'];
        if (config == null) return;

        for (var i in config) {
            var d = config[i];
            if (!d.hasOwnProperty('name')) {
                console.log("'config' value has no 'name' property.");
                continue;
            }
            var name = d['name'];
            var t = templates[name+'-template'];
            if (t == null) continue;
            rendered = template.render(t, d);
            $('#'+name).html(rendered);
        }

        common.setupDropdowns();

        $('li.backup a').bind('click', function(event) {
            event.preventDefault();
            var ts = $('span.timestamp', this).text();
            var filename = $('span.filename', this).text();

            var popupLink = $(this).hasClass('inactive');
            if (popupLink == false) {
                $('article.popup').removeClass('visible');
                $('#restore-timestamp').html(ts);
                $('#restore-filename').val(filename);
                $('article.popup#restore-dialog').addClass('visible');
            }
        });

        if ($.inArray('restore', allowed) >= 0) {
            $('li.backup a').removeClass('inactive');
        }

        $('#next-backup').html(data['next']);
    }

    function updateBackups() {
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

    function bind(id, f) {
        $(id+'-ok').bind('click', function(event) {
            event.stopPropagation();
            event.preventDefault();
            if ($(this).hasClass('inactive')) {
                return;
            }
            disableAll();
            if (f) {
                f();
            }
            $('article.popup').removeClass('visible');
        });
    }

    topic.subscribe('state', function(message, data) {
        allowed = data['allowable-actions'];
        updateState();
    });

    $().ready(function() {
        common.startMonitor();

        /* parse all page templates */
        for (var name in templates) {
            var t = $('#'+name).html();
            template.parse(t);
            templates[name] = t;
        }

        /* bind basic actions */
        for (var key in actions) {
            bind('#'+key, actions[key]);
        }

        bind('#restore', restore);
        common.setupDialogs();
    });
});
