require(['jquery', 'template', 'common', 'bootstrap', 'domReady!'],
function ($, template, common)
{
    function EditBox(node) {
        this.EDIT = 'EDIT';
        this.VIEW = 'VIEW';
        
        this.state = this.VIEW;
        this.node = node
        var value = $(node).html();
        this.value = $.trim(value);
        this.href = $(node).attr('data-href');

        this.view_template = $('#editbox-view').html();
        template.parse(this.view_template);
        this.edit_template = $('#editbox-edit').html();
        template.parse(this.edit_template);

        var html = template.render(this.view_template, {'value':this.value});
        $(node).html(html);

        this.edit = function ()
        {
            console.log("'"+this.value+"'");
            var data = {'value':this.value};
            var html = template.render(this.edit_template, data);
            $(node).html(html);
            $('input', node).focus();
            this.state = this.EDIT;
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

            $.ajax({
                type: 'POST',
                url: '/rest/profile/email',
                data: {'value':value},
                dataType: 'json',
                async: false,
            
                success: function(data) {
                    this.value = value;
                },
                error: function(req, textStatus, errorThrown) {
                    alert(textStatus + ": " + errorThrown);
                }
            });

            var html = template.render(this.view_template, {'value': value});
            $(node).html(html);
            this.state = this.VIEW;
            $('i', this.node).bind('click', function() {
                $(this).parent().data().edit();
            });
        }

        this.cancel = function ()
        {
            var data = {'value':this.value};
            var html = template.render(this.view_template, data);
            $(node).html(html);
            this.state = this.VIEW;
            $('i', this.node).bind('click', function() {
                $(this).parent().data().edit();
            });
        }


        $('i', this.node).bind('click', function() {
            $(this).parent().data().edit();
        });
    }


    $('.editbox').each(function() {
        var editbox = new EditBox($(this).get(0));
        $(this).data(editbox);
    });

    common.startup();
});
