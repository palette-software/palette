define (["dojo/dom", "dojo/request", "dojo/on",
         "dojox/widget/DialogSimple",
         "dojo/domReady"],
function(dom, request, on, DialogSimple)
{
    var uri = "/rest/backup";
    var lastBackup = dom.byId("last");

    var backupButton = dom.byId("backupButton");
    on(backupButton, "click", function() {
        request.post(uri, {
            sync: true,
            handleAs: "json",
            data: {"action": "backup"}
        }).then (
            function(d) {
                lastBackup.innerHTML = d["last"];
            },
            function(error) {
                console.log('[BACKUP] Communication Failure.');
            }
        );
    });
    

    var restoreButton = dom.byId("restoreButton");
    on(restoreButton, "click", function() {
        request.post(uri, {
            sync: true,
            handleAs: "json",
            data: {"action": "restore"}
        }).then (
            function(d) {
            },
            function(error) {
                console.log('[BACKUP] Communication Failure.');
            }
        );
    });

    var advancedLink = dom.byId("advanced-backup");
    on(advancedLink, "click", function(e) {
        e.preventDefault();
        e.stopPropagation();
        var dialog = DialogSimple({href: "/dialog/backup"});
        dialog.startup();
        dialog.show();
    });

    request.get(uri, { handleAs: "json" }).then(
        function(d) {
            lastBackup.innerHTML = d["last"];
        },
        function(error) {
            console.log('[BACKUP] Communication Failure.');
        }
    );

    return {}
});
