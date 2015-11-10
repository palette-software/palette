define(['jquery', 'cookie'],
function ($, cookie)
{
    var sidebar_open = false;
    var sidebar_enabled = false;

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
    }

    $(document).on('click.status.data-api', '[data-toggle="status"]', function (evt) {
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
            if (sidebar_enabled) {
                $('#expand-right').removeClass('fa-angle-right');
                $('#expand-right').addClass('fa-angle-left');
                filters_hidden = $('.filter-dropdowns').hasClass('hidden');
                $('.filter-dropdowns').addClass('hidden');
                sidebar_open = true;
            }
        }
    });

    $().ready(function() {
        $('.main-side-bar .status').hover(function() {
            $(this).css('cursor','pointer');
        });
    });

    return {
        'enableSidebar': enableSidebar,
        'setText': setText,
        'setColor': setColor
    };

});
