define (["dojo/dom", "dojo/dom-class", "dojo/request", "dojo/on", "dojo/topic",
         "dojox/widget/DialogSimple",
         "dojo/domReady"],
function(dom, domClass, request, on, topic, DialogSimple)
{
    var uri = "/rest/manage";
    var diskspace = dom.byId("diskspace"); // temporary

    var startButton = dom.byId("startButton");
    startButton.enabled = false;

    on(startButton, "click", function(e) {
        e.preventDefault();
        e.stopPropagation();
        if (!startButton.enabled) {
            console.log("manage: 'Start' button is disabled");
            return;
        }
        disableButtons();

        topic.publish("action-start-event", "start");
        request.post(uri, {
            sync: true,
            handleAs: "json",
            data: {"action": "start"}
        }).then (
            function(d) {
                console.log("manage: starting");
                topic.publish("action-finish-event", "manage");
            },
            function(error) {
                console.log('[MANAGE] Communication Failure.');
                topic.publish("action-finish-event", "manage");
            }
        );
    });

    var stopButton = dom.byId("stopButton");
    stopButton.enabled = true;

    on(stopButton, "click", function(e) {
        e.preventDefault();
        e.stopPropagation();
        if (!stopButton.enabled) {
            console.log("manage: 'Stop' button is disabled");
            return;
        }
        disableButtons();

        topic.publish("action-start-event", "start");
        request.post(uri, {
            sync: true,
            handleAs: "json",
            data: {"action": "stop"}
        }).then (
            function(d) {
                console.log("manage: stopping");
                topic.publish("action-finish-event", "manage");
            },
            function(error) {
                console.log('[MANAGE] Communication Failure.');
                topic.publish("action-finish-event", "manage");
            }
        );
    });

    function disableStartButton() {
        if (startButton.enabled) {
            console.log("manage: disable 'Start' button");
            startButton.enabled = false;
        }
        domClass.add(startButton, "disabled");
    }

    function disableStopButton() {
        if (stopButton.enabled) {
            console.log("manage: disable 'Stop' button");
            stopButton.enabled = false;
        }
        domClass.add(stopButton, "disabled");
    }

    function disableButtons() {
        disableStartButton();
        disableStopButton();
    }

    function enableStartButton() {
        if (!startButton.enabled) {
            console.log("manage: enable 'Start' button");
            startButton.enabled = true;
        }
        domClass.remove(startButton, "disabled");
        startButton.enabled = true;
    }

    function enableStopButton() {
        if (!stopButton.enabled) {
            console.log("manage: enable 'Stop' button");
            stopButton.enabled = true;
        }
        domClass.remove(stopButton, "disabled");
    }

    function enableButtons() {
        enableStartButton();
        enableStopButton();
    }

    topic.subscribe("action-start-event", function(name) {
        console.log("manage: start event from '" + name + "'");
        disableButtons();
    });

    topic.subscribe("status-update-event", function(data) {
        var main = data["main-state"];
        var backup = data["backup-state"];

        switch(main) {
        case "started":
            if (backup != "none") {
                disableButtons();
            } else {
                disableStartButton();
                enableStopButton();
            }
            break;
        case "stopped":
            if (backup.search("restore") == -1) {
                // Don't enable the Start button if we're stopped during restore
                enableStartButton();
                disableStopButton();
            }
            break;
        default:
            disableButtons();
        }
    });

    var advancedLink = dom.byId("advanced-manage");
    on(advancedLink, "click", function(e) {
        e.preventDefault();
        e.stopPropagation();
        var dialog = DialogSimple({href: "/dialog/manage"});
        dialog.startup();
        dialog.show();        
    });

    return {}
});
