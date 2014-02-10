define (["dojo/dom", "dojo/dom-style", "dojo/on", "dojo/request", "dojo/topic",
         "dojox/widget/DialogSimple", "palette/backup",
         "dojo/domReady"],
        function(dom, domStyle, on, request, topic, DialogSimple, backup)
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

    function setStatus(val) {
        status.innerHTML = val;
        topic.publish("status-update-event", val);
    }

    function update() {
        request.get("/rest/monitor", { handleAs: "json" }).then(
            function(data) {
                var val = data['status']
                status.innerHTML = val;
                if (val == "Running") {
                    greenLight();
                } else {
                    redLight();
                }
                setStatus(val);
            },
            function(error) {                
                status.innerHTML = 'Communication Failure.';
                redLight();
            }
        );
    }

    var timer;

    function startUpdate() {
        update();
        timer = setInterval(update, 10000);
    }

    function stopUpdate() {
        clearInterval(timer);
    }

    /* These topics control the status update timer. */
    topic.subscribe("action-start-event", function(name) {
        startUpdate();
    });
    topic.subscribe("action-finish-event", function(name) {
        stopUpdate();
    });

    startUpdate();

    var advancedLink = dom.byId("advanced-status");
    on(advancedLink, "click", function() {
        var dialog = DialogSimple({href: "/dialog/status"});
        dialog.startup();
        dialog.show();        
    });

    return {}
});
