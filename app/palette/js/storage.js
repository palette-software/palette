require(['jquery', 'template', 'common', 'OnOff', 'bootstrap'],
function ($, template, common, OnOff)
{
    common.startMonitor(false);

    var dropdown_template = $('#dropdown-template').html();
    template.parse(dropdown_template);

    function update(data) {
        /* populate the dropdowns */
        var checked = data['storage-encrypt'];
        $("#storage-encrypt .onoffswitch-checkbox").prop("checked", checked);

        checked = data['workbooks-as-twb'];
        $("#workbook-as-twb .onoffswitch-checkbox").prop("checked", checked);

        var config = data['config'];
        if (config == null) return;

        for (var i in config) {
            var data = config[i];
            var name = data['name'];

            var rendered = template.render(dropdown_template, data);
            $('#'+name).html(rendered);
        }
    }

    $.ajax({
        url: '/rest/storage',
        success: function(data) {
            $().ready(function() {
                OnOff.setup();
                update(data);
            });
        },
        error: common.ajaxError,
    });
});
