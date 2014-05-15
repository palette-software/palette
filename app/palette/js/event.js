require(['jquery', 'topic', 'template', 'common'],
function (jquery, topic, template, common)
{
    var t = $('#event-list-template').html();
    template.parse(t);   // optional, speeds up future uses

    var lastid = 0;

    var interval = 1000; // FIXME

    function update(data) {
        jquery('a.alert.errors span').html(data['red']);
        jquery('a.alert.warnings span').html(data['yellow']);
        if (!data.hasOwnProperty('events')) {
            console.log('/rest/events response did not contain "events"');
            return;
        }
        var events = data['events'];
        if (events.length == 0) {
            return;
        }
        var last = events[0];
        if (last == null) {
            return;
        }
        if (!last.hasOwnProperty('eventid')) {
            console.log('/rest/events event did not contain "eventid"');
            return;
        }
        lastid = last['eventid'];

        var html = $('#event-list').html();
        var rendered = template.render(t, data);
        html = rendered + '\n' + html;
        $('#event-list').html(html);

        common.bindEvents();
    }

    function poll() {
        var start = lastid + 1;
        var url = '/rest/events?order=desc&start='+start;
        jquery.ajax({
            url: url,
            success: function(data) {
                update(data);
            },
            complete: function() {
                setTimeout(poll, interval);
            }
        });
    }

    poll();
});
