define("items", ['jquery', 'template'],
function($, template) 
{
    /* The filter-dropdown template is in layout.mako. */
    var filter_dropdown = $('#filter-dropdown').html();
    template.parse(filter_dropdown);

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

    /*
     * configFilters
     */
    function configFilters(data) {
        for (var i in data['config']) {
            var d = data['config'][i];
            var rendered = template.render(filter_dropdown, d);
            $('#'+d['name']+'-dropdown').html(rendered);
        }
    }

    return {'bind': bind,
            'configFilters': configFilters}
});
