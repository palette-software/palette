require.config({
    paths: {
        'jquery': '/app/module/palette/js/vendor/jquery',
        'topic': '/app/module/palette/js/vendor/pubsub',
        'domReady': '/app/module/palette/js/vendor/domReady',
    }
});

require(['jquery', 'topic', 'domReady!'],
function (jquery, topic)
{
    var actionList = ['start', 'stop', 'restart']

    function disableAll() {
        for (var i in actionList) {
            $('#'+actionList[i]).addClass('inactive');
        }
    }

    function POST(action) {
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

    function start() {
        POST('start');
    }

    function stop() {
        POST('stop');
    }

    function restart() {
        alert('TBD');
    }

    function update(data) {
        if (!data.hasOwnProperty('allowable-actions')) {
            console.log("'allowable-actions' missing from JSON data.");
            return;
        }
        var allowed = data['allowable-actions'];
        for (var i in actionList) {
            var action = actionList[i];
            if (jquery.inArray(action, allowed) >= 0) {
                $('#'+action).removeClass('inactive');
            } else {
                $('#'+action).addClass('inactive');
            }
        }
    }

    function bind(id, f) {
        jquery(id).bind('click', function(event) {
            event.stopPropagation();
            event.preventDefault();
            if (jquery(this).hasClass('inactive')) {
                return;
            }
            f();
        });
    }

    bind("#start", start);
    bind("#stop", stop);
    bind("#restart", restart);

    topic.subscribe('state', function(message, data) {
        update(data);
    });
});

/* 
 * Load 'common' separately to ensure that we've subscribed to the 'state'
 * topic before the AJAX call is made - this avoids the race condition
 * between topic subscribe and the first published state.
 */
require(['common']);
