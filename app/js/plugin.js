require(['jquery', 'template', 'base'],
function ($, template)
{
    var templates = {};

    $().ready(function() {
        $('script[type="x-tmpl-mustache"]').each(function() {
            var id = $(this).attr('id');
            if (id == null) {
                id = $(this).data('id');
                if (id == null) {
                    throw "x-tmpl-mustache: missing an id.";
                }
            }
            var tmpl = $(this).html();
            template.parse(tmpl);
            templates[id] = tmpl;
        });
    });

    $.render = function(name, data) {
        /* fixme: allow name to be null i.e. use id of this */
        var tmpl = templates[name];
        if (tmpl == null) {
            throw "Template '{0}' does not exist".format(name);
            return null;
        }
        return template.render(tmpl, data);
    }

    $.fn.render = function(name, data) {
        $(this).html($.render(name, data));
    };
});
