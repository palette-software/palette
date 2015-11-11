define(['jquery', 'cookie'],
function ($, cookie)
{
    var sidebar_enabled = false;
    var SIDEBAR_WIDTH = 300;

    var content_left = null;
    var CONTENT_MIN_WIDTH = 720 + SIDEBAR_WIDTH;

    /*
     * setColor() {
     */
    function setColor(color) {

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
        cookie.set('status_color', color);
    }

    /*
     * setText() {
     */
    function setText(text) {
        $('#status-text').html(text);
        cookie.set('status_text', text);
    }

    /* Allow opening/closing the sidebar by clicking on the status div */
    function enableSidebar(value) {
        sidebar_enabled = value;
        if (value) {
            var cursor = 'pointer';
        } else {
            var cursor = 'auto';
        }
        $().ready(function() {
            $('.main-side-bar .status').hover(function() {
                $(this).css('cursor', cursor);
            });
        });
    }

    $(document).on('click.status.data-api', '[data-toggle="status"]', function (evt) {
        if (sidebar_enabled) {
            var content_width = $('.content').outerWidth();
            if ( $('.container-webapp').hasClass('servers-visible')) {
                // sidebar is open
                $('.content').css("left", content_left);
                $('.container-webapp').removeClass('servers-visible');
            } else {
                // sidebar is closed
                if (content_left == null) {
                    content_left = parseInt($('.content').css("left"));
                }
                if (content_width >= CONTENT_MIN_WIDTH) {
                    $('.content').css("left", "+=" + SIDEBAR_WIDTH.toString());
                }
                $('.container-webapp').addClass('servers-visible');
            }
        }
    });

    return {
        'enableSidebar': enableSidebar,
        'setText': setText,
        'setColor': setColor
    };

});
