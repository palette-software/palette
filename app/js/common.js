/* 
 * FIXME: This code will likely be run from the layout or side-bar
 * templates and should be named accordingly.
 */

define(['jquery', 'topic', 'status', 'paging', 'Dropdown',
        'plugin', 'cookie', 'modal', 'sidebar', 'items', 'help'],
function ($, topic, status, paging, Dropdown)
{
    /* MONITOR TIMER */
    var interval = 1000; // milliseconds
    var timer = null;
    var current = null;
    var needEvents = true;
    var filters_hidden = false;

    /*
     * EventFilter
     * pseudo-class for maintaining the selected events
     */
    var eventFilter = {
        seq: 0,
        ref: null, /* timestamp as an epoch float, microsecond resolution */
        selectors: {'status':'0', 'type':'0'},
        /* currently displayed list */
        first: 0,
        last: 0,
        count: 0,
        liveUpdate: true, /* update events on next poll cycle? */

        queryString: function () {
            var array = [];

            array.push('seq=' + ++this.seq);

            if (!needEvents) {
                array.push('event=false');
                return array.join('&');
            }

            for (var key in this.selectors) {
                var value = ddDataId(key);
                if (typeof(value) == 'undefined') {
                    continue;
                } else if (value != this.selectors[key]) {
                    this.selectors[key] = value;
                }
                if (value != '0') {
                    array.push(key+'='+value)
                }
            }

            if (paging.getPageNumber() > 1 ) {
                if (eventFilter.liveUpdate) {
                    array.push('limit='+paging.limit);
                    array.push('page='+paging.getPageNumber());
                    array.push('ref='+this.ref);
                } else {
                    array.push('event=false');
                }
            } else {
                array.push('limit='+paging.limit);
                array.push('ref='+this.ref);
            }
            return array.join('&');
        }
    }

    /*
     * gethref
     * Find the 'href' attribute of a link or the data-href of the parent div.
     * Returns null if not found or '#'.
     */
    function gethref(a) {
        var href = a.attr('href');
        if (href && href != '#') {
            return href;
        }
        var parent = a.closest('.btn-group')
        href = parent.attr('data-href');
        if (href && href != '#') {
            return href;
        }
        return null
    }

    /*
     * ddClick
     * Click handler for dropdowns : attached to the <li> tag.
     */
    function ddClick(event) {
        event.preventDefault();

        var parent = $(this).closest('.btn-group');
        var a = $(this).find('a');
        var div =  $(parent).find('div')
        var href = gethref(a)
        var id = a.attr('data-id');

        success = function(data) {
            var value = a.text();
            div.text(value);
            if (id != null) div.attr('data-id', id);
            var cb = parent.data('callback');
            if (cb) cb(parent[0], value);
        }

        if (href == null){
            success();
            return;
        }
        data = customDataAttributes(a);
        $.ajax({
            type: 'POST',
            url: href,
            data: data,
            dataType: 'json',
            async: false,

            success: success,
            error: ajaxError,
        });
    }

    /*
     * eventPageCallback(n)
     * To be called by the paging module when the current page is changed.
     */
    function eventPageCallback(n) {
        if (n != paging.getPageNumber()) {
            eventFilter.seq = 0;
        }
        /* turn on update for at least one more cycle. */
        eventFilter.liveUpdate = true;
        resetPoll();
    }

    /*
     * setupEventDropdowns()
     * Connect the Event filters to the paging mechanism - if present.
     */
    function setupEventDropdowns() {
        $('.filter-dropdowns div.btn-group').each(function () {
            $(this).data('callback', function(node, value) {
                paging.set(1);
                resetPoll();
            });
        });
    }

    /*
     * setupServerList
     * Make the individual servers in the server list visible toggle.
     */
    function setupServerList() {
        $('.server-list li a').off('click');
        $('.server-list li a').bind('click', function() {
            $(this).toggleClass('visible');
            $(this).parent().find('ul.processes').toggleClass('visible');

            var child = $(this).find('i.down-arrow');
            if (child.hasClass('fa-angle-down')) {
               child.removeClass('fa-angle-down');
               child.addClass('fa-angle-up');
            } else {
               child.removeClass('fa-angle-up');
               child.addClass('fa-angle-down');
            }
        });
    }

    /*
     * customDataAttributes
     * Return the HTML5 custom data attributes for a selector or domNode.
     */
    function customDataAttributes(obj) {
        if (obj instanceof $) {
            obj = obj.get(0);
        }
        var d = {}
        for (var i=0, attrs=obj.attributes, l=attrs.length; i<l; i++){
            var name = attrs.item(i).nodeName;
            if (!name.match('^data-')) {
                continue;
            }
            d[name.substring(5)] = attrs.item(i).value;
        }
        return d;
    }

    /*
     * updateEventList
     */
    function updateEventList(data) {
        var events = data['events'];
        if (events == null) {
            /* no update request/sent */
            return;
        }

        if (events.length == 0) {
            eventFilter.ref = null;
            eventFilter.first = 0;
            eventFilter.last = 0;
            eventFilter.count = 0;
            $('#event-list').html('');
            paging.hide();
            return;
        }

        /* checking the first eventid, the last eventid and the count is
           enough to tell if anything has changed (since events are ordered) */
        if ((events[0].eventid == eventFilter.first) && 
            (events[events.length-1].eventid == eventFilter.last) &&
            (events.length = eventFilter.count))
        {
            /* same values found. */
            return;
        }

        /* build a list of events currently opened in the UI. */
        var events_open = [];
        $('article.item.open').each(function () {
            var server = $('a > div > h5', $(this).parent()).html();
            events_open.push($(this).attr('id'));
        });

        $('#event-list').render("event-list-template", data);
        $('.filter-dropdowns').removeClass('hidden');

        for (var i=0; i < events_open.length; i++) {
            $('#' + events_open[i]).addClass('open');
        }

        eventFilter.first = events[0].eventid;
        eventFilter.last = events[events.length-1].eventid;
        eventFilter.count = events.length;

        if (paging.getPageNumber() == 1) {
            eventFilter.ref = events[0]['reference-time'];
        }

        paging.show();
    }

    /*
     * monitorUpdateEvents
     */
    function monitorUpdateEvents(data)
    {
        updateEventList(data);
        Dropdown.setupAll(data);
        paging.config(data);

        if (paging.getPageNumber() > 1) {
            eventFilter.liveUpdate = false;
        }

        setupEventDropdowns();
        paging.bind(eventPageCallback);
    }

    /*
     * monitorUpdate()
     * Returns true iff the request was not ignored and the request should
     * trigger another monitor call to be sent.
     */
    function monitorUpdate(data)
    {
        if (data['connected'] == null) {
            data['connected'] = true;
        }

        if (data['seq'] != null) {
            var n = parseInt(data['seq']);
            /* If there is more than one outstanding request, then only
             * accept the last one sent.  This can happen when a dropdown
             * is changed while a request is in-flight.
             */
            if (n != eventFilter.seq) {
                return false;
            }
        }

        /* delete seq so that the UX doesn't constantly refresh */
        delete data['seq'];

        if (data['interval'] != null) {
            interval = data['interval'];
        }
        delete data['interval'];

        var json = JSON.stringify(data);
        
        /*
         * Broadcast the state change, if applicable.
         * NOTE: this method may lead to false positives, which is OK.
         */
        if (json == current) {
            return true;
        }

        /* sidebar is only available for admins */
        status.enableSidebar(data['admin']);

        topic.publish('state', data);
        current = json;

        /* build a list of server names currently open in the UI
           FIXME: do this on a per-environment basis. */
        var servers_open = [];
        $('ul.server-list > li > ul.processes.visible').each(function () {
            var server = $('a > div > h5', $(this).parent()).html();
            servers_open.push(server);
        });

        /* Set the visible class to the processes ul for all open servers.
           FIXME: update for multi-environment support. */
        if (servers_open.length > 0) {
            for (var i = 0; i < data['environments'].length; i++) {
                var environment = data['environments'][i];
                for (var j = 0; j < environment.agents.length; j++) {
                    var agent = environment.agents[j];
                    if (servers_open.indexOf(agent.displayname) >= 0) {
                        agent.visible = 'visible';
                    }
                }
            }
        }

        var text = data['text'] != null ? data['text'] : 'SERVER ERROR';
        status.setText(text);

        var color = data['color'] != null ? data['color'] : 'red';
        status.setColor(color);

        /* FIXME: break above into separate monitorUpdateStatus() function. */

        if (data['trial-days'] != null) {
            var trial_days = data['trial-days'];
            if (trial_days == 1) {
                var msg = '1 Day Remaining';
            } else {
                var msg = data['trial-days']+' Days Remaining';
            }
            $('.navbar-announcement .trial-status').html(msg);
            if (trial_days <= 3) {
                $('.navbar-announcement').addClass('urgent');
            }


            var url = data['buy-url'];
            $('.navbar-announcement .trial-subscribe a').prop('href', url);
            $('.navbar-announcement').height("37px");

            /* this makes the content scrollbar work properly */
            var margin = $(".navbar").height() + 37;
            $('.content').css("margin-bottom", margin.toString() + "px");
        } else {
            $('.navbar-announcement').remove();
            var margin = $(".navbar").height();
            $('.content').css("margin-bottom", margin.toString() + "px");
        }

        if (data['environments'] != null) {
            var envs = data['environments'];
            if ((envs.length > 0) && (envs[0]['agents'].length > 0)) {
                $('#server-list').render("server-list-template", data);
                setupServerList();
            }
        }

        if (needEvents) {
            monitorUpdateEvents(data);
        }
        return true;
    }

    /*
     * disableEvents
     * Don't retrieve events in the monitor for pages that don't use them.
     */
    function disableEvents(){
        needEvents = false;
    }

    /*
     * ddDataId
     * Get the data-id of the current selection in a particular dropdown.
     * '0' is always 'all' or 'unset'.
     * fixme: move to dropdown.js
     */
    function ddDataId(name) {
        var selector = "#"+name+'-dropdown > button > div';
        return $(selector).attr('data-id');
    }

    function poll() {
        var url = '/rest/monitor?'+eventFilter.queryString();

        $.ajax({
            url: url,
            success: function(data) {
                $().ready(function() {
                    var retval = monitorUpdate(data);
                    if (retval) {
                        timer = setTimeout(poll, interval);
                    }
                });
            },
            error: function(req, textStatus, errorThrown)
            {
                $().ready(function() {
                    var data = {}
                    data['text'] = 'Your Browser is Disconnected';
                    data['color'] = 'yellow';
                    data['connected'] = false;
                    monitorUpdate(data); /* can't return false. */
                    timer = setTimeout(poll, interval);
                });
            }
        });
    }

    function resetPoll() {
        if (timer != null) {
            clearTimeout(timer);
        }
        eventFilter.seq = 0;
        poll();
    }

    /*
     * startMonitor
     * The optional 'arg' is passed directly to the global needEvents.
     */
    function startMonitor(arg) {
        needEvents = (typeof arg === "undefined") ? true : arg;
        /* 
         * Start a timer that periodically polls the status every
         * 'interval' milliseconds
         */
        poll();
    }

    /*
     * ajaxError
     * Common routine for displaying AJAX error messages.
     */
    function ajaxError(jqXHR, textStatus, errorThrown) {
        var msg = jqXHR.status + " (" + errorThrown + ")";
        if (this.url != null) {
            msg = this.url + ':' + msg;
        }
        if (jqXHR.responseText != null) {
            var $dom = $($.parseHTML(jqXHR.responseText));
            var str = $("<div>").html(jqXHR.responseText)
                .contents()
                .filter(function() {
                    return this.nodeType == Node.TEXT_NODE;
                }).text();
            str = str.replace(/\s+/g, ' ');
            msg += '\n' + str.trim();
        }
        alert(msg);
        //location.reload();
    }

    return {'startMonitor': startMonitor,
            'ajaxError': ajaxError,
            'setupEventDropdowns' : setupEventDropdowns,
           };
});
