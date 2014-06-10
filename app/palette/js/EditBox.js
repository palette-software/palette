define("EditBox", ['jquery', 'template'],
function($, template) {

    var EDIT = 'EDIT';
    var VIEW = 'VIEW';

    function EditBox(node, callback) {
        this.state = VIEW;
        this.node = node
        this.callback = callback;
        var value = $(node).html();
        this.value = $.trim(value);
        this.id = $(node).attr('data-id');
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
            $('.ok', this.node).bind('click', function(event) {
                event.stopPropagation();
                $(this).parent().data().ok();
            });
            $('.cancel', this.node).bind('click', function(event) {
                event.stopPropagation();
                $(this).parent().data().cancel();
            });
        }

        this.ok = function ()
        {
            var value = $('input', this.node).val();
            var data = {'value':value}
            if (this.id != null) {
                data['id'] = this.id;
            }
            if (this.name != null) {
                data['name'] = this.name;
            }
            var success;

            if (this.href) {
                $.ajax({
                    type: 'POST',
                    url: this.href,
                    data: data,
                    dataType: 'json',
                    async: false,
            
                    success: function(data) {
                        success = true;
                    },
                    error: function(req, textStatus, errorThrown) {
                        alert('[ERROR] ' + textStatus + ": " + errorThrown);
                        sucess = false;
                    }
                });
            } else {
                success = true;
            }

            if (success) {
                this.value = value;
            } else {
                value = this.value;
            }

            var html = template.render(this.view_template, {'value': value});
            $(node).html(html);
            this.state = VIEW;

            if (success) {
                if (this.callback) {
                    this.callback(value);
                }
            }

            $('i', this.node).bind('click', function(event) {
                event.stopPropagation();
                $(this).parent().data().edit();
            });
        }

        this.cancel = function ()
        {
            var data = {'value':this.value};
            var html = template.render(this.view_template, data);
            $(node).html(html);
            this.state = VIEW;
            $('i', this.node).bind('click', function(event) {
                event.stopPropagation();
                $(this).parent().data().edit();
            });
        }

        $('i', this.node).bind('click', function(event) {
            event.stopPropagation();
            $(this).parent().data().edit();
        });
    }

    EditBox.bind = function (selector, callback) {
        var array = [];
        $(selector).each(function() {
            var editbox = new EditBox($(this).get(0), callback);
            $(this).data(editbox);
            array.push(editbox);
        });
        if (array.length == 0) return null;
        return array.length > 1 ? array : array[0];
    }

    EditBox.setup = function(callback)
    {
        EditBox.bind('.editbox', callback);
    }

    return EditBox;
});
