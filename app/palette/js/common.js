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

    var lastid = 0; /* last event id */

     /*
     * bindStatus()
     * Make the clicking on the status box show the server list.
     */
    function bindStatus() {
        $('.main-side-bar .status').off('click');
        $('.main-side-bar .status').bind('click', function() {
            $('.main-side-bar li.active, .secondary-side-bar, .dynamic-content, .secondary-side-bar.servers').toggleClass('servers-visible');
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
        /* HEADER POPUP MENUS */
        var viewport = $(window).width();

        $('#mainNav ul.nav li.more').bind('mouseenter', function() {
            if (viewport >= 960) {
        	    $('#mainNav ul.nav li.more ul').removeClass('visible');
                $(this).find('ul').addClass('visible');
            }
        });
        $('#mainNav ul.nav li.more').bind('mouseleave', function() {
            if (viewport >= 960) {
                $(this).find('ul').removeClass('visible');
            }
        });     
        
        $('#mainNav ul.nav li.more a').bind('click', function() {
            if (viewport <= 960) {
                event.preventDefault();
            }

        });

        $('#mainNav ul.nav li.more').bind('click', function() {
            if (viewport <= 960) {
                var navOpen = $(this).find('ul').hasClass('visible'); 
                $('#mainNav ul.nav li.more').find('ul').removeClass('visible');
                if (navOpen) {
                    $(this).find('ul').removeClass('visible');
                }
                else {
                    $(this).find('ul').addClass('visible');
                }           
            } 
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
     * setupDropdowns()
     * Enable the select-like elements created with the dropdown class.
     */
    function setupDropdowns() {
        $('.dropdown-menu li').off('click');
        $('.dropdown-menu li').bind('click', function(event) {
            event.preventDefault();
            var a = $(this).find('a');
            var div =  $(this).parent().siblings().find('div')
            var href = a.attr('href');
            if (!href || href == '#') {
                div.text(a.text());
                return;
            }
            data = customDataAttributes(a);
            $.ajax({
                type: 'POST',
                url: href,
                data: data,
                dataType: 'json',
                async: false,
            
                success: function(data) {
                    div.text(a.text());
                },
                error: common.ajaxError,
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
            d[name.substring(5)] = attrs.item(i).nodeValue;
        }
        return d;
    }

    /*
     * updateEvents
     */
    function updateEvents(data) {
        $('a.alert.errors span').html(data['red']);
        $('a.alert.warnings span').html(data['yellow']);

        var events = data['events'];
        if (events == null || events.length == 0) {
            return;
        }
        var last = events[0];
        if (last == null) {
            return;
        }
        if (!last.hasOwnProperty('eventid')) {
            return;
        }
        lastid = last['eventid'];

        var html = $('#event-list').html();
        var rendered = template.render(event_list_template, data);
        html = rendered + '\n' + html;
        $('#event-list').html(html);

        bindEvents();
    }

    /* Code run automatically when 'common' is included */
    $().ready(function() {        

        /*
        $('#mainNav .container > i').bind('click', function() {
            $('.main-side-bar, .secondary-side-bar, .dynamic-content').toggleClass('open');
	        $(this).toggleClass('open');
        });
        */
        setupHeaderMenus();
        setupCategories();
        setupDropdowns();
        bindStatus();
    });


    /* MONITOR TIMER */
    var interval = 1000; //ms - FIXME: make configurable from the backend.
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

    function poll() {
        var start = lastid + 1;
        var url = '/rest/monitor?order=desc&start='+start+'&high=50';

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
                setTimeout(poll, interval);
            }
        });
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
            'startMonitor': startMonitor,
            'ajaxError': ajaxError,
            'bindEvents': bindEvents,
            'setupDialogs': setupDialogs,
            'setupDropdowns' : setupDropdowns,
            'setupServerList' : setupServerList
           };
});
