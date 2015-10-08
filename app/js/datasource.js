require(['jquery', 'template', 'common', 'paging', 'items',
         'Dropdown', 'EditBox', 'bootstrap'],
function ($, template, common, paging, items, Dropdown, EditBox)
{
    var t = $('#datasource-list-template').html();
    template.parse(t);

    /*
     * siteDropdownCallback()
     * Clear the project selection when the site selection changes.
     */
    function siteDropdownCallback(id, value) {
        paging.set(1);
        Dropdown.setValueById('project-dropdown', 0);
        query();
    }

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
        var publisher_only = data['publisher-only'];

        /* all vs. my datasources doesn't make sense for publishers */
        if (publisher_only) {
            $("#show-dropdown").addClass('hidden');
        } else {
            $("#show-dropdown").removeClass('hidden');
        }

        /* does this table have any items? */
        var populated = data['enabled'];
        if (populated) {
            $(".filter-dropdowns").removeClass('hidden');
            var rendered = template.render(t, data);
            $('#datasource-list').html(rendered);
            items.bind();
        } else {
            $(".filter-dropdowns").addClass('hidden');
            if (publisher_only) {
                $('.admin-only').remove();
                $('.publisher-only').removeClass('hidden');
            } else {
                $('.publish-only').remove();
                $('.admin-only').removeClass('hidden');
            }
        }

        EditBox.setup();
        Dropdown.setupAll(data);

        paging.config(data);
        paging.bind(wbPageCallback);
        paging.show();

        // selection change callback.
        $('.filter-dropdowns div.btn-group').each(function () {
            if ($(this).attr('id') == 'site-dropdown') {
                $(this).data('callback', siteDropdownCallback);
            } else {
                $(this).data('callback', function(id, value) {
                    paging.set(1);
                    query();
                });
            }
        });

        // prevent the link from opening/closing the event.
        $('.event > div.summary a').bind('click', function(event) {
            event.stopPropagation();
        });

        var siteid = Dropdown.getValueById('site-dropdown');
        if (siteid == "0") {
            $('#project-dropdown > button').addClass('disabled');
        } else {
            $('#project-dropdown > button').removeClass('disabled');
        }

    }

    /*
     * query()
     * Send an AJAX request to the rest handler.
     */
    function query() {
        var url = '/rest/datasources' + queryString();
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

    /*
     * wbPageCallback(n)
     * To be called by the paging module when the current page is changed.
     */
    function wbPageCallback(n) {
        query();
    }

    query();
    common.startMonitor(false);
});
