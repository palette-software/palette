require(['jquery', 'topic', 'template', 'common',
         'bootstrap', 'event', 'domReady!'],
function (jquery, topic, template, common)
{
    /*
     * bindStatus()
     * Make the clicking on the status box show the server list.
     */
    function bindStatus() {
        $('.main-side-bar .status').bind('click', function() {
            $('.secondary-side-bar, .dynamic-content, .secondary-side-bar.servers').toggleClass('servers-visible');
        });
    }

    var t = $('#server-list-template').html();
    template.parse(t);   // optional, speeds up future uses

    bindStatus();

    topic.subscribe('state', function (message, data) {
        var rendered = template.render(t, data);
        $('#server-list').html(rendered);

        /* FIXME: copied from common.js */
        $('.server-list li a').bind('click', function() {
            $(this).toggleClass('visible');
            $(this).parent().find('ul.processes').toggleClass('visible');
        });
    });

    common.startup();
    common.setupDropdowns();
});

