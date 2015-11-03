define(['jquery'],
function($)
{
    /*
     * bind()
     * Expand/contract the individual items on user click.
     * NOTE: Must be run after:
     *  - the AJAX request which populates the list.
     *  - the document is ready.
     */
    function bind() {
        $('.item > div.summary').off('click');
        $('.item > div.summary').bind('click', function() {
            $(this).parent().toggleClass('open');
            $(this).find('i.expand').toggleClass("fa-angle-up fa-angle-down");
        });
    }

    $(document).on('click.item.data-api', '[data-toggle="item"]', function (evt) {
        var $item = $(this).closest(".item");
        $item.toggleClass('open');
        /* fixme */
        $('i.expand', $item).toggleClass("fa-angle-up fa-angle-down");
    });
});
