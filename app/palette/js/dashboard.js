require.config({
    paths: {
        'jquery': '/app/module/palette/js/vendor/jquery',
        'topic': '/app/module/palette/js/vendor/pubsub',
        'template' : '/app/module/palette/js/vendor/mustache',
        'domReady': '/app/module/palette/js/vendor/domReady',
    }
});

require(['jquery', 'topic', 'template', 'common'],
function (jquery, topic, template)
{
    var t = $('#server-list-template').html();
    template.parse(t);   // optional, speeds up future uses

    topic.subscribe('state', function (message, data) {
        var rendered = template.render(t, data);
        $('#server-list').html(rendered);
    });
});
