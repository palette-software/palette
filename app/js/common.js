/* 
 * FIXME: This code will likely be run from the layout or side-bar
 * templates and should be named accordingly.
 */

define(['jquery', 'topic', 'items', 'paging', 'Dropdown',
        'plugin', 'modal'],
function ($, topic, items, paging, Dropdown)
{
    /* MONITOR TIMER */
    var interval = 1000; // milliseconds
    var timer = null;
    var current = null;
    var needEvents = true;

    var status_color = null;
    var status_text = null;

    var sidebar_open = false;
    var status_bound = false;

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
     * setCookie()
     */
    function setCookie(cname, cvalue, exdays) {
        var value = cname + "=" + cvalue.replace(" ", "_");
        if (exdays != undefined) {
            var d = new Date();
            d.setTime(d.getTime() + (exdays*24*60*60*1000));
            value += "; expires="+d.toUTCString();
        }
        value += "; path=" + "/";
        document.cookie = value;
    }

    /*
     * deleteCookie()
     * Delete a cookie by name by setting it to expire.
     */
    function deleteCookie(name) {
        document.cookie = name + '=;expires=Thu, 01 Jan 1970 00:00:01 GMT;';
    }

    /*
     * getCookie()
     */
    function getCookie(cname) {
        var name = cname + "=";
        var ca = document.cookie.split(';');
        for(var i=0; i < ca.length; i++) {
            var c = ca[i];
            while (c.charAt(0)==' ') {
                c = c.substring(1);
            }
            if (c.indexOf(name) != -1) {
                return c.substring(name.length, c.length).toString();
            }
        }
        return null;
    }

     /*
     * bindStatus()
     * Make the clicking on the status box show the server list.
     */
    function bindStatus() {
        $('.main-side-bar .status').off('click');
        $('.main-side-bar .status').bind('click', function() {
            $('.main-side-bar li.active, ' +
              '.secondary-side-bar, .dynamic-content, ' +
              '.secondary-side-bar.servers').toggleClass('servers-visible');
            if (sidebar_open) {
                $('#expand-right').removeClass('fa-angle-left');
                $('#expand-right').addClass('fa-angle-right');
                if (!filters_hidden) {
                    $('.filter-dropdowns').removeClass('hidden');
                }
                sidebar_open = false;
            } else {
                $('#expand-right').removeClass('fa-angle-right');
                $('#expand-right').addClass('fa-angle-left');
                filters_hidden = $('.filter-dropdowns').hasClass('hidden');
                $('.filter-dropdowns').addClass('hidden');
                sidebar_open = true;
            }
        });
        $('.main-side-bar .status').hover(function() {
            $(this).css('cursor','pointer');
        });
        status_bound = true;
    }

    /*
     * setupHeaderMenus
     * Enable the popup menus in the navigation bar.
     */
    function setupHeaderMenus()
    {
        $('#mainNav ul.nav li.more').bind('mouseenter', function() {
            $('#mainNav ul.nav li.more ul').removeClass('visible');
            $(this).find('ul').addClass('visible');
        });
        $('#mainNav ul.nav li.more').bind('mouseleave', function() {
            $(this).find('ul').removeClass('visible');
        });     
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
     * setupCategories
     * Enable the configure expansion item on main sidebar.
     */
    function setupCategories() {
        $('.expand').parent().off('click');
        $('.expand').parent().bind('click', function(event) {
            event.preventDefault();
            if ($('.expand', this).hasClass('fa-angle-down')) {
                $('.expand', this).removeClass('fa-angle-down');
                $('.expand', this).addClass('fa-angle-up');
                $(this).parent().find('ul').addClass('visible');
            } else {
                $('.expand', this).removeClass('fa-angle-up');
                $('.expand', this).addClass('fa-angle-down');
                $(this).parent().find('ul').removeClass('visible');
            }                
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
     * setStatusColor() {
     */
    function setStatusColor(color) {

        if (color == status_color)
            return;

        var $i = $('#status-icon')

        /* FIXME: do this with LESS */
        if (color == 'green') {
            $i.removeClass('fa-exclamation-circle yellow');
            $i.removeClass('fa-times-circle red');
            $i.addClass('fa-check-circle green');
        } else if (color == 'yellow') {
            $i.removeClass('fa-check-circle green');
            $i.removeClass('fa-times-circle red');
            $i.addClass('fa-exclamation-circle yellow');
        } else if (color == 'red') {
            $i.removeClass('fa-check-circle green');
            $i.removeClass('fa-exclamation-circle yellow');
            $i.addClass('fa-times-circle red');
        } else {
            return;
        }
        status_color = color;
        setCookie('status_color', color);
    }

    /*
     * setStatusText() {
     */
    function setStatusText(text) {

        if (text == status_text)
            return;

        $('#status-text').html(text);
        status_text = text;
        setCookie('status_text', text);
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

        items.bind();

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

        var admin = data['admin'];
        if (admin && !status_bound) {
            bindStatus();
        }

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
        setStatusText(text);

        var color = data['color'] != null ? data['color'] : 'red';
        setStatusColor(color);

        /* FIXME: break above into separate monitorUpdateStatus() function. */

        if (data['nav-message'] != null) {
            $('#mainNav .message').html(data['nav-message']);
        } else if (data['trial-days'] != null) {
            var msg = 'Trial Status: <span class="highlight">';
            if (data['trial-days'] == 1) {
                msg += '1 Day Remaining';
            } else {
                msg += data['trial-days']+' Days Remaining';
            }
            msg += '</span>';
            $('#mainNav .message').html(msg);
        } else {
            $('#mainNav .message').html('');
        }

        if (data['trial-days'] == null) {
            $('#mainNav li.buy').addClass('hidden');
        } else {
            $('#mainNav li.buy').removeClass('hidden');
            if (data['trial-days'] <= 3) {
                $('#mainNav li.buy, #mainNav .message').addClass('urgent');
            } else {
                $('#mainNav li.buy, #mainNav .message').removeClass('urgent');
            }
        }
        $('#mainNav li.buy a').prop('href', data['buy-url']);

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
                var retval = monitorUpdate(data);
                if (retval) {
                    timer = setTimeout(poll, interval);
                }
            },
            error: function(req, textStatus, errorThrown)
            {
                var data = {}
                data['text'] = 'Your Browser is Disconnected';
                data['color'] = 'yellow';
                data['connected'] = false;
                monitorUpdate(data); /* can't return false. */
                timer = setTimeout(poll, interval);
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

    /*
     * lightbox()
     * Create lightboxes that bind to the help icons.
     * Requires 'lightbox'
     */
    function lightbox(id, title) {
        /* The title is now ignored but keeping it improves code readablity
           where this function is called (gives a keyword to the id number.) */
        var lb = new TopicLightBox({
            baseUrl: 'http://kb.palette-software.com',
            id: id,
            title: ' ',
            background: true,
            width: 800,
            height: 500
        });
    }

    /* Code run automatically when 'common' is included */
    $().ready(function() {
        setupHeaderMenus();
        setupCategories();
    });

    return {'startMonitor': startMonitor,
            'ajaxError': ajaxError,
            'getCookie': getCookie,
            'setCookie': setCookie,
            'deleteCookie': deleteCookie,
            'lightbox': lightbox,
            'setupEventDropdowns' : setupEventDropdowns,
           };
});
