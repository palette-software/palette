define(['jquery'],
function($)
{

    /*
     * Open/close the individual items on user click.
     */
    $(document)
        .on('click.item.data-api', '[data-toggle="item"]',
            function (evt) {
                var $item = $(this).closest(".item");
                $item.toggleClass('open');
            });
});
