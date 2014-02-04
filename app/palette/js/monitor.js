define (["dojo/dom", "dojo/dom-style", "dojo/on", "dojo/request",
         "dojox/widget/DialogSimple",
         "dojo/domReady"],
        function(dom, domStyle, on, request, DialogSimple)
{
    var status = dom.byId("status-message");
    var green = dom.byId("green");
    var orange = dom.byId("green");
    var red = dom.byId("green");

    function greenLight() {
        domStyle.set("orange", "display", "none");
        domStyle.set("red", "display", "none");
        domStyle.set("green", "display", "block");
    }

    function orangeLight() {
        domStyle.set("green", "display", "none");
        domStyle.set("red", "display", "none");
        domStyle.set("orange", "display", "block");
    }

    function redLight() {
        domStyle.set("green", "display", "none");
        domStyle.set("orange", "display", "none");
        domStyle.set("red", "display", "block");
    }

    function update() {
        request.get("/rest/monitor", { handleAs: "json" }).then(
            function(data) {
                status.innerHTML = data['status'];
                if (data['status'] == 'RUNNING') {
                    greenLight();
                } else {
                    redLight();
                }
            },
            function(error) {                
                status.innerHTML = 'Communication Failure.';
                redLight();
            }
        );
    }

    update();
    var timer = setInterval(function() {
        update();
    }, 10000);

    var advancedLink = dom.byId("advanced-status");
    on(advancedLink, "click", function() {
        var dialog = DialogSimple({href: "/dialog/status"});
        dialog.startup();
        dialog.show();        
    });

    return {}
});
