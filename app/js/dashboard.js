require(['jquery', 'common', 'Dropdown', 'tableau', 'bootstrap'],
function ($, common, Dropdown)
{
    var viz = null;

    /*
     * callback()
     */
    function callback(id, value) {
        console.log(value);
        
        var placeholderDiv = document.getElementById('tableauViz');
        var url = 'https://demo-tableau.palette-software.com/views/PaletteDashboards/' + id;
        var options = {
            width: placeholderDiv.offsetWidth - 250,
            height: 900,
            hideTabs: true,
            hideToolbar: true,
            onFirstInteractive: function () {
                workbook = viz.getWorkbook();
                activeSheet = workbook.getActiveSheet();
            }
        };
        if (viz != null) {
            viz.dispose();
        }
        viz = new tableau.Viz(placeholderDiv, url, options);
    }

    /*
     * update(data)
     * Handle a successful response from an AJAX request.
     */
    function update(data) {
        Dropdown.setupAll(data, callback);
        callback(data['config'][0]['id'], data['config'][0]['value']);
    }

    common.startMonitor(false);

    $.ajax({
        url: '/rest/dashboard',
        success: function(data) {
            $().ready(function() {
                update(data);
            });
        },
        error: common.ajaxError
    });
});

