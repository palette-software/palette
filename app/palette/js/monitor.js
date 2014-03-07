define (["dojo/dom", "dojo/dom-style", "dojo/on", "dojo/request", "dojo/topic",
         "dojox/widget/DialogSimple", "palette/backup",
         "dojo/domReady"],
        function(dom, domStyle, on, request, topic, DialogSimple, backup)
{
    var status = dom.byId("status-message");
    var green = dom.byId("green");
    var yellow = dom.byId("yellow");
    var orange = dom.byId("orange");
    var red = dom.byId("red");

    function greenLight() {
        domStyle.set("yellow", "display", "none");
        domStyle.set("orange", "display", "none");
        domStyle.set("red", "display", "none");
        domStyle.set("green", "display", "block");
    }

    function orangeLight() {
        domStyle.set("green", "display", "none");
        domStyle.set("yellow", "display", "none");
        domStyle.set("red", "display", "none");
        domStyle.set("orange", "display", "block");
    }

    function yellowLight() {
        domStyle.set("green", "display", "none");
        domStyle.set("orange", "display", "none");
        domStyle.set("red", "display", "none");
        domStyle.set("yellow", "display", "block");
    }

    function redLight() {
        domStyle.set("green", "display", "none");
        domStyle.set("yellow", "display", "none");
        domStyle.set("orange", "display", "none");
        domStyle.set("red", "display", "block");
    }

    function setStatus(data) {
        if (data["main-state"]) {
            var main = data["main-state"];
            var backup = "none";
            if (data["backup-state"]) {
                backup = data["backup-state"];
            }

            switch (main) {
            case "started":
                if (backup == "backup") {
                    status.innerHTML = "OK, backup in progress";
                } else {
                    status.innerHTML = "OK";
                }
                greenLight();
                break;
            case "stopped":
                status.innerHTML = "Stopped";
                redLight();
                break;
            case "starting":
                status.innerHTML = "Starting ...";
                yellowLight();
                break;
            case "stopping":
                if (backup == "backup") {
                    status.innerHTML = "Stopping for restore ...";
                } else {
                    status.innerHTML = "Stopping ...";
                }
                yellowLight();
                break;
            default:
                status.innerHTML = main;
                redLight();
                break;
            }
        } else {
            status.innerHTML = 'Communication Error: Bad Response';
            redLight();
        }
        topic.publish("status-update-event", data);
        console.log("monitor: status-update-event " + JSON.stringify(data));
    }

    function update() {
        request.get("/rest/monitor", { handleAs: "json" }).then(
            function(data) {
                setStatus(data);
            },
            function(error) {
                data["main-state"] = "Communication Failure.";
                setStatus(data);
            }
        );
    }

    var timer;

    function startUpdate() {
        console.log("monitor: starting update timer");
        update();
        timer = setInterval(update, 10000);
    }

    function stopUpdate() {
        console.log("monitor: stopping update timer.");
        clearInterval(timer);
        console.log("monitor: update timer stopped");
    }

    /* These topics control the status update timer. */
    topic.subscribe("action-start-event", function(name) {
        stopUpdate();
    });
    topic.subscribe("action-finish-event", function(name) {
        startUpdate();
    });

    startUpdate();

    var advancedLink = dom.byId("advanced-status");
    on(advancedLink, "click", function(e) {
        e.preventDefault();
        e.stopPropagation();
        var dialog = DialogSimple({href: "/dialog/status"});
        dialog.startup();
        dialog.show();        
    });

    return {}
});
