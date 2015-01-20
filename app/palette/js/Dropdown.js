define("Dropdown", ['jquery', 'template'],
function($, template) {

    function Dropdown(node, data, callback, error) {
        this.node = node;
        this.callback = callback;
        this.error = error;
        this.options = {}

        this.template = $('#dropdown-template').html();
        template.parse(this.template);

        for (var i in data['options']) {
            var option = data['options'][i];
            this.options[option.id] = option.item;
        }

        var html = template.render(this.template, data);
        $(node).html(html);

        this.set = function (id) {
            value = this.options[id]
            var $div = $('button > div', this.node);
            $div.attr('data-id', id);
            $div.text(value);
            if (this.callback) {
                this.callback(id, value);
            }
        }

        this.getDataId = function () {
            var $div = $('button > div', this.node);
            return $div.attr('data-id');
        }

        this.change = function (id, value) {
            var success;
            if (this.href) {
                $.ajax({
                    type: 'POST',
                    url: this.href,
                    data: {'id': id, 'value': value},
                    dataType: 'json',
                    async: false,

                    success: function(data) {
                        success = true;
                    },
                    error: function (jqXHR, textStatus, errorThrown) {
                        if (this.error) {
                            this.error(jqXHR, textStatus, errorThrown);
                        } else {
                            alert(this.url + ": " +
                                  jqXHR.status + " (" + errorThrown + ")");
                        }
                        sucess = false;
                    }
                });
            } else {
                success = true;
            }

            if (success) {
                this.set(id);
            }
        }

        $('.dropdown-menu li a', this.node).off('click');
        $('.dropdown-menu li a', this.node).bind('click', function(event) {
            /* don't stop propagation - it 'closes' the dropdown. */
            /* $(this) is the <a> tag in the <li> selected. */
            var id = $(this).attr('data-id');
            $(this).closest('.btn-group').data().change(id, $(this).text());
        });
    }

    Dropdown.bind2 = function(id, data, callback)
    {
        var $this = $('#' + id);
        var obj = new Dropdown($this.get(0), data, callback);
        $this.data(obj);
    }

    /*
     * 'data' looks like:
     *   {'name': '...', 'id': X, 'value': '...',
     *    'options': [{'id': Y, 'item': '...'}, ... ]}
     */
    Dropdown.setup = function(data, callback)
    {
        return Dropdown.bind2(data['name'], data, callback);
    }

    /*
     * iterate through the 'config' items and create dropdowns.
     */
    Dropdown.setupAll = function(data, callback)
    {
        for (var i in data['config']) {
            Dropdown.setup(data['config'][i]);
        }
    }

    Dropdown.getValueById = function(id)
    {
        var dd = $('#' + id).data();
        return dd.getDataId();
    }

    Dropdown.setValueById = function(id, value)
    {
        var dd = $('#' + id).data();
        return dd.set(value);
    }

    Dropdown.setCallback = function(selector, callback)
    {
        $(selector).each(function (index) {
            var dd = $(this).data();
            dd.callback = callback;
        });
    }

    return Dropdown;
});

