require(['jquery', 'topic', 'template', 'common',
         'event', 'bootstrap', 'domReady!'],
function (jquery, topic, template, common)
{
    var actions = {'start': start,
                   'stop': stop,
                   'backup': backup};

    var templates = {'backup-list-template': null,
                     'archive-backup-template': null};

    var allowed = [];

    function disableAll() {
        /* FIXME - do this with a class */
        for (var action in actions) {
            $('#'+action).addClass('inactive');
        }
    }

    function managePOST(action) {
        jquery.ajax({
            type: 'POST',
            url: '/rest/manage',
            data: {'action': action},
            dataType: 'json',
            async: false,
            
            success: function(data) {},
            error: function(req, textStatus, errorThrown) {
                alert(textStatus);
            }
        });
    }

    function start() {
        managePOST('start');
    }

    function stop() {
        managePOST('stop');
    }

    function backup() {
        jquery.ajax({
            type: 'POST',
            url: '/rest/backup',
            data: {'action': 'backup'},
            dataType: 'json',
            async: false,
            
            success: function(data) {},
            error: function(req, textStatus, errorThrown) {
                alert(textStatus + ': ' + errorThrown);
            }
        });
    }

    function restore() {
        var ts = jquery('#restore-timestamp').html();
        var filename = jquery('#restore-filename').val();

        jquery.ajax({
            type: 'POST',
            url: '/rest/backup',
            data: {'action': 'restore',
                   'filename': filename},
            dataType: 'json',
            async: false,
            
            success: function(data) {},
            error: function(req, textStatus, errorThrown) {
                alert(textStatus);
            }
        });
    }

    function updateState(data) {
        if (!data.hasOwnProperty('allowable-actions')) {
            console.log("'allowable-actions' missing from JSON data.");
            return;
        }
        
        allowed = data['allowable-actions'];
        for (var action in actions) {
            if (jquery.inArray(action, allowed) >= 0) {
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
            jquery('#'+name).html(rendered);
        }

        common.setupDropdowns();

        jquery('li.backup a').bind('click', function(event) {
            event.preventDefault();
            var ts = jquery('span.timestamp', this).text();
            var filename = jquery('span.filename', this).text();

            var popupLink = $(this).hasClass('inactive');
            if (popupLink == false) {
                jquery('article.popup').removeClass('visible');
                jquery('#restore-timestamp').html(ts);
                jquery('#restore-filename').val(filename);
                jquery('article.popup#restore-dialog').addClass('visible');
            }
        });

        if (jquery.inArray('restore', allowed) >= 0) {
            jquery('li.backup a').removeClass('inactive');
        }

        jquery('#next-backup').html(data['next']);
    }

    function updateBackups() {
        jquery.ajax({
            url: '/rest/backup',
            success: function(data) {
                updateBackupSuccess(data);
            },
            error: function(req, textStatus, errorThrown) {
                console.log('[backup] ' + textStatus + ': ' + errorThrown);
            },
        });
    }

    function bind(id, f) {
        jquery(id+'-ok').bind('click', function(event) {
            event.stopPropagation();
            event.preventDefault();
            if (jquery(this).hasClass('inactive')) {
                return;
            }
            disableAll();
            f();
            jquery('article.popup').removeClass('visible');
        });
    }

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
    common.setupDropdowns();

    topic.subscribe('state', function(message, data) {
        updateState(data);
    });

    common.startup();
});
