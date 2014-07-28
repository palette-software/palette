require(['jquery', 'template', 'common', 'EditBox', 'OnOff'],
function ($, template, common, EditBox, OnOff)
{
    function change() {
        var node = $(this).get(0);
        var id = $(this).attr('data-id');
        var value = $(this).is(":checked");
        $.ajax({
            type: 'POST',
            url: '/rest/servers/archive',
            data: {'id':id, 'value':value},
            dataType: 'json',
            async: false,
            success: function(data) {},
            error: function(jqXHR, textStatus, errorThrown) {
                common.ajaxError(jqXHR, textStatus, errorThrown);
                $(node).prop("checked", !value);
            }
        });
    }

    function update(data) {
        $().ready(function() {
            var t = $('#server-detail-template').html();
            var rendered = template.render(t, data);
            $('#server-detail').html(rendered);
            common.bindEvents();
            EditBox.bind('.editbox.displayname');
            EditBox.bind('.editbox.environment', function(value) {
                $('.editbox.environment >span').html(value);
            });
            $('input[type="checkbox"]').change(change);
            OnOff.setup();
        });
    }

    $.ajax({
        url: '/rest/servers',
        success: function(data) {
            update(data);
        },
        error: common.ajaxError,
    });

    common.startMonitor();
});
