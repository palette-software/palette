require(['jquery', 'template', 'common', 'paging', 'items',
         'Dropdown', 'EditBox', 'bootstrap'],
function ($, template, common, paging, items, Dropdown, EditBox)
{
    var t = $('#workbook-list-template').html();
    template.parse(t);

    /*
     * queryString()
     * Build a query string based on the state of the selectors.
     *
     * NOTE: The result of the first call is an empty string,
     *       since the selectors are populated by update()
     */
    function queryString() {
        var array = [];
        $('.filter-dropdowns div > button > div').each(function () {
            var name = $(this).parent().parent().attr('id');
            if (name != null) {
                name = name.replace('-dropdown', '');
                array.push(name + '=' + $(this).attr('data-id'));
            }
        });
        array.push('page=' + paging.getPageNumber().toString());
        array.push('limit=' + paging.limit);
        return '?' + array.join('&');
    }

    /*
     * update(data)
     * Handle a successful response from an AJAX request.
     */
    function update(data) {
        var rendered = template.render(t, data);
        $('#workbook-list').html(rendered);

        items.bind();
        EditBox.setup();
        Dropdown.setupAll(data);

        paging.config(data);
        paging.show();
        common.setupEventDropdowns();

        // selection change callback.
        $('.filter-dropdowns div.btn-group').each(function () {
            $(this).data('callback', function(node, value) {
                query();
            });
        });

        // prevent the link from opening/closing the event.
        $('.event > div.summary a').bind('click', function(event) {
            event.stopPropagation();
        });
    }

    /*
     * query()
     * Send an AJAX request to the rest handler.
     */
    function query() {
        var url = '/rest/workbooks' + queryString();
        $.ajax({
            url: url,
            success: function(data) {
                $().ready(function() {
                    update(data);
                });
            },
            error: common.ajaxError
        });
    }

    query();
    common.startMonitor(false);
});
