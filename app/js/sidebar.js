define(['jquery'],
function($)
{
    /*
     * Open/close the sidebar categories on user click.
     */
    $(document).on('click.category.data-api', '[data-toggle="category"]',
        function (evt) {
            var $item = $(this).closest(".category");
            $item.toggleClass('open');
            evt.preventDefault();
        });
});

