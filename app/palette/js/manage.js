require.config({
    paths: {
        'jquery': '/app/module/palette/js/vendor/jquery',
        'topic': '/app/module/palette/js/vendor/pubsub',
        'template' : '/app/module/palette/js/vendor/mustache',
        'domReady': '/app/module/palette/js/vendor/domReady',
    }
});

require(['jquery', 'topic', 'template', 'event', 'domReady!'],
function (jquery, topic, template)
{
    var actions = {'start': start,
                   'stop': stop,
                   'restart': restart,
                   'backup': backup,
                   'restore': restore};

    var templates = {'backup-list-template': null,
                     'archive-backup-template': null};

    function disableAll() {
        for (var action in actions) {
            $('#'+action).addClass('inactive');
        }
    }

    function managePOST(action) {
        disableAll();
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

    function backupPOST(action) {
        disableAll();
        jquery.ajax({
            type: 'POST',
            url: '/rest/backup',
            data: {'action': action},
            dataType: 'json',
            async: false,
            
            success: function(data) {},
            error: function(req, textStatus, errorThrown) {
                alert(textStatus + ': ' + errorThrown);
            }
        });
    }

    function start() {
        managePOST('start');
    }

    function stop() {
        managePOST('stop');
    }

    function restart() {
        alert('TBD');
    }

    function backup() {
        backupPOST('backup');
    }

    function restore() {
        backupPOST('restore');
    }

    function updateState(data) {
        if (!data.hasOwnProperty('allowable-actions')) {
            console.log("'allowable-actions' missing from JSON data.");
            return;
        }
        var allowed = data['allowable-actions'];
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

        /*
         * FIXME: (from common.js) Re-bind since this code runs after the
         * AJAX request has returned - the HTML isn't ready in the first bind. 
         */
        jquery('.dropdown-menu li').bind('click', function(event) {
            event.preventDefault();
            var dropdownSelect = jquery(this).find('a').text();
            jquery(this).parent().siblings().find('div').text(dropdownSelect);
        });

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

    for (var key in actions) {
        bind('#'+key, actions[key]);
    }

    topic.subscribe('state', function(message, data) {
        updateState(data);
    });
});

/* 
 * Load 'common' separately to ensure that we've subscribed to the 'state'
 * topic before the AJAX call is made - this avoids the race condition
 * between topic subscribe and the first published state.
 */
require(['common']);
