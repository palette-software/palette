/* 
 * FIXME: This code will likely be run from the layout or side-bar
 * templates and should be named accordingly.
 */

define(['jquery', 'topic', 'template', 'items', 'paging'],
function ($, topic, template, items, paging)
{
    var server_list_template = $('#server-list-template').html();
    template.parse(server_list_template);

    var event_list_template = $('#event-list-template').html();
    template.parse(event_list_template);

    /* MONITOR TIMER */
    var interval = 1000; //ms - FIXME: make configurable from the backend.
    var timer = null;
    var current = null;
    var needEvents = true;

    var status_color = null;
    var status_text = null;

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

            array.push('seq='+this.seq++);

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
        value += "; path=/";
        document.cookie = value;
    }

    /*
     * getCookie()
     */
    function getCookie(cname) {
        var name = cname + "=";
        var ca = document.cookie.split(';');
        for(var i=0; i<ca.length; i++) {
            var c = ca[i];
            while (c.charAt(0)==' ') {
                c = c.substring(1);
            }
            if (c.indexOf(name) != -1)
                return c.substring(name.length, c.length);
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
            if ($('#expand-right').hasClass('fa-angle-right')) {
                $('#expand-right').removeClass('fa-angle-right');
                $('#expand-right').addClass('fa-angle-left');
                $('.filter-dropdowns').addClass('hidden');
            } else {
                $('#expand-right').removeClass('fa-angle-left');
                $('#expand-right').addClass('fa-angle-right');
                $('.filter-dropdowns').removeClass('hidden');
            }
        });
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
     * setupDialogs()
     * Connect dialogs to their relevant click handlers.
     */
    function setupDialogs()
    {
        $('a.popup-link').bind('click', function() {
            var popupLink = $(this).hasClass('inactive');
            if (popupLink == false) {
                $('article.popup').removeClass('visible');
                var popTarget = $(this).attr('name');
                $('article.popup#'+popTarget).addClass('visible');
            }
        });

        $('.popup-close, article.popup .shade').bind('click', function() {
            $('article.popup').removeClass('visible');
        });
    }

    /*
     * setupOkCancel()
     * Instantiate the generic OK/Cancel dialog.
     */
    function setupOkCancel()
    {
        $().ready(function() {
            $('#okcancel .popup-ok').bind('click', function() {
                var data = $(this).closest('article').data();
                var callback = data['callback'];
                if (callback != null) {
                    callback($(this));
                }
                $('#okcancel').removeClass('visible');
            });

            $('#okcancel .popup-close').bind('click', function() {
                $('#okcancel').removeClass('visible');
            });

            $('#okcancel .shade').bind('click', function() {
                $('#okcancel').removeClass('visible');
            });

            $('.okcancel').bind('click', function() {
                var data = $(this).data();
                var inactive = $(this).hasClass('inactive');
                if (inactive == false) {
                    /* link button data to the article. */
                    $('#okcancel').data(data);
                    var text = data['text'];
                    if (text == null) {
                        text = $(this).attr('data-text');
                    }
                    $('#okcancel p').html(text);
                    $('#okcancel').addClass('visible');
                }
            });
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
     * setupDropdowns()
     * Enable the select-like elements created with the dropdown class.
     */
    function setupDropdowns() {
        $('.dropdown-menu li').off('click');
        $('.dropdown-menu li').bind('click', ddClick);
    }

    /*
     * setupEventDropdowns()
     * Enable the Event filters - if present.
     */
    function setupEventDropdowns() {
        setupDropdowns()
        $('.filter-dropdowns div.btn-group').each(function () {
            $(this).data('callback', function(node, value) {
                paging.set(1);
                resetPoll();
            });
        });
    }

    /*
     * setupConfigure
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

        var rendered = template.render(event_list_template, data);
        $('#event-list').html(rendered);

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
        items.configFilters(data);
        paging.config(data);

        if (paging.getPageNumber() > 1) {
            eventFilter.liveUpdate = false;
        }

        items.bind();

        /* FIXME: do these once. */
        setupEventDropdowns();
        paging.bind(eventPageCallback);
    }

    function monitorUpdate(data)
    {
        if (data['connected'] == null) {
            data['connected'] = true;
        }

        var json = JSON.stringify(data);
        
        /*
         * Broadcast the state change, if applicable.
         * NOTE: this method may lead to false positives, which is OK.
         */
        if (json == current) {
            return;
        }

        topic.publish('state', data);
        current = json;

        var text = data['text'] != null ? data['text'] : 'SERVER ERROR';
        setStatusText(text);

        var color = data['color'] != null ? data['color'] : 'red';
        setStatusColor(color);

        /* FIXME: break above into separate monitorUpdateStatus() function. */

        var rendered = template.render(server_list_template, data);
        $('#server-list').html(rendered);
        setupServerList();

        if (needEvents) {
            monitorUpdateEvents(data);
        }
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
                monitorUpdate(data);
            },
            error: function(req, textStatus, errorThrown)
            {
                var data = {}
                data['text'] = 'Browser Disconnected';
                data['color'] = 'yellow';
                data['connected'] = false;
                monitorUpdate(data);
            },
            complete: function() {
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
        alert(this.url + ': ' + jqXHR.status + " (" + errorThrown + ")");
        location.reload();
    }

    /* Code run automatically when 'common' is included */
    $().ready(function() {
        setupHeaderMenus();
        setupCategories();
        bindStatus();
    });

    return {'startMonitor': startMonitor,
            'ajaxError': ajaxError,
            'setupDialogs': setupDialogs,
            'setupDropdowns' : setupDropdowns,
            'setupOkCancel' : setupOkCancel,
           };
});
