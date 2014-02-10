define (["dojo/dom", "dojo/dom-class", "dojo/request", "dojo/on", "dojo/topic",
         "dojox/widget/DialogSimple",
         "dojo/domReady"],
function(dom, domClass, request, on, topic, DialogSimple)
{
    var uri = "/rest/backup";
    var lastBackup = dom.byId("last");

    var backupButton = dom.byId("backupButton");
    on(backupButton, "click", function() {
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
    on(restoreButton, "click", function() {
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

    topic.subscribe("action-start-event", function(name) {
        domClass.add(backupButton, "disabled");
        domClass.add(restoreButton, "disabled");
    });

    topic.subscribe("status-update-event", function(val) {
        console.log("backup: got status update event");
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
