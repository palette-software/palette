/* 
 * FIXME: This code will likely be run from the layout or side-bar
 * templates and should be named accordingly.
 */

define(['jquery', 'topic', 'template'],
function ($, topic, template)
{
    var server_list_template = $('#server-list-template').html();
    template.parse(server_list_template);

    var event_list_template = $('#event-list-template').html();
    template.parse(event_list_template);

    var event_dropdown_template = $('#event-dropdown-template').html();
    template.parse(event_dropdown_template);

     /*
     * bindStatus()
     * Make the clicking on the status box show the server list.
     */
    function bindStatus() {
        $('.main-side-bar .status').off('click');
        $('.main-side-bar .status').bind('click', function() {
            $('.main-side-bar li.active, .secondary-side-bar, .dynamic-content, .secondary-side-bar.servers').toggleClass('servers-visible');
            if ($('#expand-right').hasClass('fa-angle-right')) {
                $('#expand-right').removeClass('fa-angle-right');
                $('#expand-right').addClass('fa-angle-left');
            } else {
                $('#expand-right').removeClass('fa-angle-left');
                $('#expand-right').addClass('fa-angle-right');
            }
        });
    }

    /*
     * bindEvents()
     * Expand/contract the individual events on user click.
     * NOTE: Must be run after the AJAX request which populates the list.
     */
    function bindEvents() {
        $('.event > div.summary').off('click');
        $('.event > div.summary').bind('click', function() {
            $(this).parent().toggleClass('open');
            $(this).find('i.expand').toggleClass("fa-angle-up fa-angle-down");
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
     * setPage(n)
     */
    function setPage(n) {
        eventFilter.page = n;
        /* turn on update for at least one more cycle. */
        eventFilter.liveUpdate = true;
        resetPoll();
    }

    /*
     * pageCount()
     */
    function pageCount() {
        n = (eventFilter.count + eventFilter.limit -1) / eventFilter.limit;
        return Math.floor(n);
    }

    /*
     * nextPage()
     */
    function nextPage(event) {
        event.preventDefault();
        event.stopPropagation();
        if (eventFilter.page < pageCount()) {
            setPage(eventFilter.page+1);
        }
    }

    /*
     * prevPage()
     */
    function prevPage(event) {
        event.preventDefault();
        event.stopPropagation();
        if (eventFilter.page > 1) {
            setPage(eventFilter.page-1);
        }
    }

    /*
     * firstPage()
     */
    function firstPage(event) {
        event.preventDefault();
        event.stopPropagation();
        setPage(1);
    }

    /*
     * nextPage()
     */
    function lastPage(event) {
        event.preventDefault();
        event.stopPropagation();
        setPage(pageCount());
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
        $('.dropdown-menu li').off('click');
        $('.dropdown-menu li').bind('click', ddClick);
        $('.event-dropdowns div.btn-group').each(function () {
            $(this).data('callback', function(node, value) {
                eventFilter.page = 1;
                resetPoll();
            });
        });
    }

    /*
     * setupEventPagination()
     * Enable the next, previous, etc links.
     */
    function setupEventPagination() {
        $('#event-pagination .next a').off('click');
        $('#event-pagination .next a').bind('click', nextPage);
        $('#event-pagination .previous a').off('click');
        $('#event-pagination .previous a').bind('click', prevPage);
        $('#event-pagination .first a').off('click');
        $('#event-pagination .first a').bind('click', firstPage);
        $('#event-pagination .last a').off('click');
        $('#event-pagination .last a').bind('click', lastPage);
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
            eventFilter.current['first'] = 0;
            eventFilter.current['last'] = 0;
            eventFilter.current['count'] = 0;
            $('#event-list').html('');
            return;
        }

        /* checking the first eventid, the last eventid and the count is
           enough to tell if anything has changed (since events are ordered) */
        if ((events[0].eventid == eventFilter.current['first']) && 
            (events[events.length-1].eventid == eventFilter.current['last']) &&
            (events.length = eventFilter.current['count']))
        {
            /* same values found. */
            return;
        }

        var rendered = template.render(event_list_template, data);
        $('#event-list').html(rendered);

        eventFilter.current['first'] = events[0].eventid;
        eventFilter.current['last'] = events[events.length-1].eventid;
        eventFilter.current['count'] = events.length;

        if (eventFilter.page == 1) {
            eventFilter.ref = events[0]['reference-time'];
        }
    }

    /*
     * updateEvents
     */
    function updateEvents(data) {

        updateEventList(data);

        for (var i in data['config']) {
            var d = data['config'][i];
            rendered = template.render(event_dropdown_template, d);
            $('#'+d['name']+'-dropdown').html(rendered);
        }

        var count = data['event-count'];
        if (count != null) {
            $('#event-count span').html(count);
            eventFilter.count = count;
            $('#event-pagination .page-number').html(eventFilter.page);
            $('#event-pagination .page-count').html(pageCount());
        }

        if (eventFilter.page > 1) {
            eventFilter.liveUpdate = false;
        }

        bindEvents();

        /* FIXME: do these once. */
        setupEventDropdowns();
        setupEventPagination();
    }

    /* Code run automatically when 'common' is included */
    $().ready(function() {
        setupHeaderMenus();
        setupCategories();
        bindStatus();
    });


    /* MONITOR TIMER */
    var interval = 1000; //ms - FIXME: make configurable from the backend.
    var timer = null;
    var current = null;

    function update(data)
    {
        var state = data['state']
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
        $('#status-text').html(text);

        var color = data['color'] != null ? data['color'] : 'red';
        var src = '/app/module/palette/images/status-'+color+'-light.png';
        $('#status-image').attr('src', src);

        updateEvents(data);

        var rendered = template.render(server_list_template, data);
        $('#server-list').html(rendered);
        setupServerList();
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

    /*
     * EventFilter
     * pseudo-class for maintaining the selected events
     */
    var eventFilter = {
        page: 1,
        limit: 25,
        count: 0,
        ref: null, /* timestamp as an epoch float, microsecond resolution */
        selectors: {'status':'0', 'type':'0'},
        current: {'first':0,'last':0, 'count':0}, /* currently displayed list */
        liveUpdate: true, /* update events on next poll cycle? */

        queryString: function () {
            var array = [];
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

            if (this.page > 1 ) {
                if (eventFilter.liveUpdate) {
                    array.push('limit='+this.limit);
                    array.push('page='+this.page);
                    array.push('ref='+this.ref);
                } else {
                    array.push('event=false');
                }
            } else {
                array.push('limit='+this.limit);
            }
            return array.join('&');
        }
    }

    function poll() {
        var url = '/rest/monitor?'+eventFilter.queryString();

        $.ajax({
            url: url,
            success: function(data) {
                update(data);
            },
            error: function(req, textStatus, errorThrown)
            {
                var data = {}
                data['text'] = 'Browser Disconnected';
                data['color'] = 'yellow';
                update(data);
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
        poll();
    }

    function startMonitor() {
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

    return {'state': current,
            'customDataAttributes': customDataAttributes,
            'startMonitor': startMonitor,
            'ajaxError': ajaxError,
            'bindEvents': bindEvents,
            'setupDialogs': setupDialogs,
            'setupDropdowns' : setupDropdowns,
            'setupServerList' : setupServerList
           };
});
