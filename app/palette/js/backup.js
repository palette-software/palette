define (["dojo/dom", "dojo/dom-class", "dojo/request", "dojo/on", "dojo/topic",
         "dojox/widget/DialogSimple",
         "dojo/domReady"],
function(dom, domClass, request, on, topic, DialogSimple)
{
    var uri = "/rest/backup";
    var lastBackup = dom.byId("last");
    var secondary = "none";

    var backupButton = dom.byId("backupButton");
    backupButton.enabled = true;

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
    restoreButton.enabled = true;

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

    function disableBackupButton() {
        if (backupButton.enabled) {
            console.log("backup: disable 'Backup' button");
            backupButton.enabled = false;
        }
        domClass.add(backupButton, "disabled");
    }

    function disableRestoreButton() {
        if (restoreButton.enabled) {
            console.log("backup: disable 'Restore' button");
            restoreButton.enabled = false;
        }
        domClass.add(restoreButton, "disabled");
    }


    function disableButtons() {
        disableBackupButton();
        disableRestoreButton();
    }

    function enableBackupButton() {
        if (!backupButton.enabled) {
            console.log("backup: enable 'Backup' button");
            backupButton.enabled = true;
        }
        domClass.remove(backupButton, "disabled");
    }

    function enableRestoreButton() {
        if (!restoreButton.enabled) {
            console.log("backup: enable 'Restore' button");
            restoreButton.enabled = true;
        }
        domClass.remove(restoreButton, "disabled");
    }


    function enableButtons() {
        enableBackupButton();
        enableRestoreButton();
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
