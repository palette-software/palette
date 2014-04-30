require.config({
    paths: {
        'jquery': '/app/module/palette/js/vendor/jquery',
        'topic': '/app/module/palette/js/vendor/pubsub',
        'domReady': '/app/module/palette/js/vendor/domReady',
    }
});

/* 
 * FIXME: This code will likely be run from the layout or side-bar
 * templates and should be named accordingly.
 */

require(['jquery', 'topic', 'domReady!'],
function (jquery, topic)
{
    var interval = 10000; //ms
    var current = null;

    function update(data)
    {
        var state = null;
        if (data.hasOwnProperty('state') && data['state'] != 'none') {
            state = data['state'];
        }
        
        /* Broadcast the state change, if applicable. */
        if (state != current) {
            topic.publish('state', data);
            current = state;
        }

        var text = 'ERROR';
        if (data.hasOwnProperty('text') && data['text'] != 'none') {
            text = data['text'];
        }
        jquery('#status-text').html(text);

        var color = 'red';
        if (data.hasOwnProperty('color') && data['color'] != 'none') {
            color = data['color'];
        }
        var src = '/app/module/palette/images/status-'+color+'-light.png';
        jquery('#status-image').attr('src', src);
    }

    function poll() {
        jquery.ajax({
            url: '/rest/monitor',
            success: function(data) {
                update(data);
            },
            error: function(req, textStatus, errorThrown)
            {
                var data = {}
                data['text'] = textStatus;
                update(data);
            },
            complete: function() {
                setTimeout(poll, interval);
            }
        });
    }

    /* 
     * Start a timer that periodically polls the status every
     * 'interval' milliseconds
     */
    poll();
});
