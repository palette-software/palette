require(['jquery', 'template', 'common', 'EditBox', 'bootstrap'],
function ($, template, common, EditBox)
{
    common.startMonitor();

    /*
     * customDataAttributes
     * Return the HTML5 custom data attributes for a selector or domNode.
     */
    
    function customDataAttributes(obj) {
        if (obj instanceof $) {
            obj = obj.get(0);
        }
        var d = {}
        for (var i=0, attrs=obj.attributes, l=attrs.length; i<l; i++){
            var name = attrs.item(i).nodeName;
            if (!name.match('^data-')) {
                continue;
            }
            d[name.substring(5)] = attrs.item(i).nodeValue;
        }
        return d;
    }

    /*
     * getDataHREF
     * Returns the HTML5 custom data attributes for an object or any of its parents
     */
    function getDataHREF(obj) {
        var i = obj;
        while (i) {
            if (i.hasAttribute("data-href"))
            {
                return i.attributes['data-href'].value;
            }
            i = i.parentNode;
        }
    }

    function update(data) {
        /* populate the settings */
        result = data.storage[0];
        $("#disk-watermark-low").val(result["disk-watermark-low"]);
        $("#disk-watermark-high").val(result["disk-watermark-high"]);
        $("#storage-encrypt").prop("checked", result["storage-encrypt"] == "yes");
        $("#num-auto-backups").val(result["num-auto-backups"]);
        $("#num-other-backups").val(result["num-other-backups"]);
        $("#archive-twb").val(result["archive-twb"]);
        $("#backup-auto-retain-count").val(result["backup-auto-retain-count"]);
        $("#backup-user-retain-count").val(result["backup-user-retain-count"]);

        /* populate the volumes dropdown */
        result = data.storage[1]["volumes"]
        var t = $('#storage-dropdown-template').html();
        var rendered = template.render(t, result);
        $("#storage-dropdown").html(rendered);
    }

    $().ready(function() {
        $('.refresh > span').bind('click', function() {
            refresh();
        });
        $('.onoffswitch-inner').toggleClass("yesnoswitch-inner");

        $('.numeric').bind("input", function () { 
          this.value = this.value.replace(/[^0-9\.]/g,'');
        });
    
        $('.data-enabled').bind("change", function() {
            attributes = customDataAttributes(this);

            name = attributes['name'];
            url = getDataHREF(this);

            if (name == "undefined" || url == "undefined") {
                console.log('Error: data-name name or data-href');
                return;
            }

            data = {'id': name, 'value': this.value | this.checked}; 

            $.ajax({
                type: 'POST',
                url: url,
                data: data,
                dataType: 'json',
                async: false,

                success: function(data) {
                    update(data);
                },
                error: common.ajaxError,
            });
        });

    });

    $.ajax({
        url: '/rest/storage',
        success: function(data) {
            update(data);
        },
        error: common.ajaxError,
    });
});
