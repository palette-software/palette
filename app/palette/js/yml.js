require(['jquery', 'template', 'common', 'domReady!'],
function (jquery, template, common)
{
    var t = jquery('#yml-list-template').html();
    template.parse(t);

    function update(data) {
        var rendered = template.render(t, data);
        $('#yml-list').html(rendered);
    }

    jquery.ajax({
        url: '/rest/yml',
        success: function(data) {
            update(data);
        },
        error: function(req, textStatus, errorThrown) {
            console.log('[ERROR] '+textStatus+': '+errorThrown);
        },
    });

    common.startup();
});