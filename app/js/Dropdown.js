define("Dropdown", ['jquery', 'plugin', 'bootstrap'],
function($) {

    function Dropdown(node, data, callback, error) {
        this.node = node;
        this.callback = callback;
        this.error = error;
        this.options = {}
        this.href = $(node).attr('data-href');

        for (var i in data['options']) {
            var option = data['options'][i];
            this.options[option.id.toString()] = option.item;
        }

        this.original_html = $(node).html();
        $(node).render('dropdown-template', data);

        this.set = function (id) {
            var value = this.options[id];
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

        this.customDataAttributes = function () {
            var d = {}
            for (var i=0, attrs=node.attributes, l=attrs.length; i<l; i++){
                var name = attrs.item(i).nodeName;
                if (!name.match('^data-') || name == 'data-href') {
                    continue;
                }
                d[name.substring(5)] = attrs.item(i).value;
            }
            return d;
        }

        this.change = function (id, value) {
            var success;
            if (this.href) {
                var data = this.customDataAttributes();
                data['id'] = id;
                data['value'] = value;

                $.ajax({
                    type: 'POST',
                    url: this.href,
                    data: data,
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

    Dropdown.bind = function(selector, data, callback)
    {
        $(selector).each(function() {
            var obj = new Dropdown(this, data, callback);
            $(this).data(obj);
        });
    }

    Dropdown.bind2 = function(id, data, callback)
    {
        var $this = $($.jq(id));
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
        try {
            var dd = $($.jq(id)).data();
            return dd.getDataId();
        } catch (err) {
            return null;
        }
    }

    Dropdown.setValueById = function(id, value)
    {
        var dd = $('#' + id).data();
        return dd.set(value);
    }

    Dropdown.getValueByNode = function(node)
    {
        try {
            var dd = $(node).data();
            return dd.getDataId();
        } catch (err) {
            return null;
        }
    }

    Dropdown.setValueByNode = function(node, value)
    {
        var dd = $(node).data();
        return dd.set(value);
    }

    Dropdown.setCallback = function(callback, selector)
    {
        if (selector == null) {
            selector = '.btn-group';
        }
        $(selector).each(function (index) {
            var dd = $(this).data();
            dd.callback = callback;
        });
    }

    return Dropdown;
});

