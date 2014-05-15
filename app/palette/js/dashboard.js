require(['jquery', 'topic', 'template', 'event', 'domReady!'],
function (jquery, topic, template)
{
    var t = $('#server-list-template').html();
    template.parse(t);   // optional, speeds up future uses

    /* STATUS BUTTON */
    $('.main-side-bar .status').bind('click', function() {
        $('.secondary-side-bar, .dynamic-content, .secondary-side-bar.servers').toggleClass('servers-visible');
    });

    topic.subscribe('state', function (message, data) {
        var rendered = template.render(t, data);
        $('#server-list').html(rendered);

        /* FIXME: copied from common.js */
        $('.server-list li a').bind('click', function() {
            $(this).toggleClass('visible');
            $(this).parent().find('ul.processes').toggleClass('visible');
        });
    });
});

require(['common']);
