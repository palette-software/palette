define(['jquery', 'lightbox'],
function($)
{
    var baseUrl = 'http://kb.palette-software.com';

    /*
     * Open the help lightbox on user click.
     * 'id' and data-toggle="help" are both required
     */
    $(document)
        .on('click.help.data-api', '[data-toggle="help"]',
            function (evt) {
                var id = $(this).attr('id');
                if (!id) {
                    console.log('[ERROR] help icon is missing id');
                    return;
                }
                $(this).off('click');
                /* only get here the first click */
                var lb = new TopicLightBox({
                    baseUrl: baseUrl,
                    id: id,
                    title: ' ',
                    background: true,
                    width: 800,
                    height: 500
                });
                evt.stopPropagation();

                /* re-click so that lb gets the event */
                $(this).click();
            });
});
