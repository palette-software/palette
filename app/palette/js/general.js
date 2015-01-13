require(['jquery', 'template', 'common', 'EditBox', 'OnOff', 'bootstrap'],
function ($, template, common, EditBox, OnOff)
{
    common.startMonitor(false);

    var dropdown_template = $('#dropdown-template').html();
    template.parse(dropdown_template);

    function change_storage_location(value) {
        $('#s3, #gcs, #local').addClass('hidden');
        if (value != 'none') {
            $('#' + value).removeClass('hidden');
        }
    }

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
        url: '/rest/general',
        success: function(data) {
            $().ready(function() {
                update(data);
                EditBox.setup();
                OnOff.setup();
                common.setupDropdowns();
            });
        },
        error: common.ajaxError,
    });

    $.ajax({
        url: '/rest/storage',
        success: function(data) {
            $().ready(function() {
                $('input:radio[name="storage-type"]').change(function() {
                    change_storage_location($(this).val());
                });
                $('#storage-'+data['storage-type']).prop('checked', true);
                change_storage_location(data['storage-type']);
            });
        },
        error: common.ajaxError,
    });
});
