define("EditBox", ['jquery', 'template'],
function($, template) {

    var EDIT = 'EDIT';
    var VIEW = 'VIEW';

    function EditBox(node) {
        this.state = VIEW;
        this.node = node
        var value = $(node).html();
        this.value = $.trim(value);
        this.name = $(node).attr('data-name');
        this.href = $(node).attr('data-href');

        this.view_template = $('#editbox-view').html();
        template.parse(this.view_template);
        this.edit_template = $('#editbox-edit').html();
        template.parse(this.edit_template);

        var html = template.render(this.view_template, {'value':this.value});
        $(node).html(html);

        this.edit = function ()
        {
            var data = {'value':this.value};
            var html = template.render(this.edit_template, data);
            $(node).html(html);
            $('input', node).focus();
            this.state = EDIT;
            $('.ok', this.node).bind('click', function() {
                $(this).parent().data().ok();
            });
            $('.cancel', this.node).bind('click', function() {
                $(this).parent().data().cancel();
            });
        }

        this.ok = function ()
        {
            var value = $('input', this.node).val();
            var data = {'value':value}
            if (this.name != null) {
                data['name'] = this.name;
            }

            if (this.href) {
                $.ajax({
                    type: 'POST',
                    url: this.href,
                    data: data,
                    dataType: 'json',
                    async: false,
            
                    success: function(data) {
                        this.value = value;
                    },
                    error: function(req, textStatus, errorThrown) {
                        alert('[ERROR] ' + textStatus + ": " + errorThrown);
                    }
                });
            } else {
                this.value = value;
            }

            var html = template.render(this.view_template, {'value': value});
            $(node).html(html);
            this.state = VIEW;
            $('i', this.node).bind('click', function() {
                $(this).parent().data().edit();
            });
        }

        this.cancel = function ()
        {
            var data = {'value':this.value};
            var html = template.render(this.view_template, data);
            $(node).html(html);
            this.state = VIEW;
            $('i', this.node).bind('click', function() {
                $(this).parent().data().edit();
            });
        }

        $('i', this.node).bind('click', function() {
            $(this).parent().data().edit();
        });
    }

    EditBox.setup = function()
    {
        $('.editbox').each(function() {
            var editbox = new EditBox($(this).get(0));
            $(this).data(editbox);
        });
    }

    return EditBox;
});
