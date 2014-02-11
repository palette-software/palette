define (["dojo/dom", "dojo/dom-class", "dojo/request", "dojo/on", "dojo/topic",
         "dojox/widget/DialogSimple",
         "dojo/domReady"],
function(dom, domClass, request, on, topic, DialogSimple)
{
    var uri = "/rest/backup";
    var lastBackup = dom.byId("last");
    var secondary = "none";

    var backupButton = dom.byId("backupButton");
    on(backupButton, "click", function(e) {
        e.preventDefault();
        e.stopPropagation();
        disableButtons();
        if (secondary != "none") {
            return;
        }
        topic.publish("action-start-event", "backup");
        request.post(uri, {
            sync: true,
            handleAs: "json",
            data: {"action": "backup"}
        }).then (
            function(d) {
                lastBackup.innerHTML = d["last"];
                topic.publish("action-finish-event", "backup");
            },
            function(error) {
                console.log('[BACKUP] Communication Failure.');
                topic.publish("action-finish-event", "backup");
            }
        );
    });
    

    var restoreButton = dom.byId("restoreButton");
    on(restoreButton, "click", function(e) {
        e.preventDefault();
        e.stopPropagation();
        disableButtons();
        if (secondary != "none") {
            return;
        }
        topic.publish("action-start-event", "restore");
        request.post(uri, {
            sync: true,
            handleAs: "json",
            data: {"action": "restore"}
        }).then (
            function(d) {
                topic.publish("action-finish-event", "restore");
            },
            function(error) {
                console.log('[BACKUP] Communication Failure.');
                topic.publish("action-finish-event", "restore");
            }
        );
    });

    function disableButtons() {
        console.log("backup: disable buttons");
        domClass.add(backupButton, "disabled");
        domClass.add(restoreButton, "disabled");
    }

    function enableButtons() {
        console.log("backup: enable buttons");
        domClass.remove(backupButton, "disabled");
        domClass.remove(restoreButton, "disabled");
    }

    topic.subscribe("action-start-event", function(name) {
        console.log("backup: start event from '" + name + "'");
        disableButtons();
    });

    topic.subscribe("status-update-event", function(data) {
        var main = data["main-state"];
        var secondary = data["secondary-state"];

        if (data["last-backup"]) {
            lastBackup.innerHTML = data['last-backup'];
        }

        switch (main) {
        case "started":
            if (secondary == "backup" || secondary == "restore") {
                disableButtons();
            } else {
                enableButtons();
            }
            break;
        default:
            disableButtons();
        }
    });

    var advancedLink = dom.byId("advanced-backup");
    on(advancedLink, "click", function(e) {
        e.preventDefault();
        e.stopPropagation();
        var dialog = DialogSimple({href: "/dialog/backup"});
        dialog.startup();
        dialog.show();
    });

    return {}
});
