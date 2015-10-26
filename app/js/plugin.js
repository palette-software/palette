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

    /*
     * Escape selector characters in 'id'.
     * see: learn.jquery.com -> jq().
     */
    $.jq = function jq(id) {
        return "#" + id.replace( /(:|\.|\[|\]|,)/g, "\\$1" );
    }

    /*
     * Render a template and return the resulting html.
     */
    $.render = function(name, data) {
        /* fixme: allow name to be null i.e. use id of this */
        var tmpl = templates[name];
        if (tmpl == null) {
            throw "Template '{0}' does not exist".format(name);
            return null;
        }
        return template.render(tmpl, data);
    }

    /*
     * Replace the html of selected elements with the rendered template.
     */
    $.fn.render = function(name, data) {
        $(this).html($.render(name, data));
    };
});
