/* 
 * FIXME: This code will likely be run from the layout or side-bar
 * templates and should be named accordingly.
 */

define(['jquery', 'topic', 'domReady!'],
function (jquery, topic)
{
    /* MOBILE TITLE */
    $(function(){
        var pageTitle = $('title').text();
        pageTitle = pageTitle.replace('Palette - ', '');
        
        $('.mobile-title').text(pageTitle);
    });

    /* POPUPS */
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

    /* SERVER LIST */
    $('.server-list li a').bind('click', function() {
        $(this).toggleClass('visible');
        $(this).parent().find('ul.processes').toggleClass('visible');
    });

    /* SIDEBAR */
    $('#toggle-side-menu').bind('click', function() {
	    $('.main-side-bar, .secondary-side-bar, .dynamic-content').toggleClass('collapsed');
    });

    $('#mainNav .container > i').bind('click', function() {
        $('.main-side-bar, .secondary-side-bar, .dynamic-content').toggleClass('open');
	    $(this).toggleClass('open');
    });

    function clearmenu() {
	$('.main-side-bar, .secondary-side-bar, .dynamic-content').removeClass('open');
	$('.main-side-bar, .secondary-side-bar, .dynamic-content').removeClass('collapsed');
	$('#mainNav .container > i').removeClass('open');
    }

    /* EVENTS */
    $('.event').bind('click', function() {
        $(this).toggleClass('open');
    });

    $('#toggle-event-filters').bind('click', function() {
        $(this).toggleClass('open');
        $('.top-zone').find('.btn-group').toggleClass('visible');
    });

    $(function(){
        $('.dynamic-content').bind('click', function() {
            var viewport = $(window).width();
            var dynamicClosed = $(this).hasClass('closed');
            if (viewport <= 960 && dynamicClosed != true) {
                clearmenu();
                $('.secondary-side-bar, .dynamic-content').toggleClass('closed');
                $('#toggle-events').toggleClass('active');
            }
        }); 
    });

    $(function(){
        $('.secondary-side-bar').bind('click', function() {
            var viewport = $(window).width();
            var dynamicClosed = $(this).hasClass('closed');
            if (viewport <= 960 && dynamicClosed == true) {
                clearmenu();
                $('.secondary-side-bar, .dynamic-content').toggleClass('closed');
                $('#toggle-events').toggleClass('active');
            }
        }); 
    });

    $(function(){
        $('#toggle-events').bind('click', function() {
            clearmenu();
            $('.secondary-side-bar, .dynamic-content').toggleClass('closed');
            $(this).toggleClass('active');
        }); 
    });

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

    /* DROP DOWN FUNCTIONALITY */
    $('.dropdown-menu li').bind('click', function() {
        var dropdownSelect = $(this).find('a').text();     
        $(this).parent().siblings().find('div').text(dropdownSelect);
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
         * NOTE: this method may lead to false positive, which is OK.
         */
        if (json != current) {
            topic.publish('state', data);
            current = json;
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
        //jquery('#status-text').attr("class", color);
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

    return {'state': current };

});
