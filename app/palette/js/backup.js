define (["dojo/dom", "dojo/request", "dojo/on", "dojo/domReady"],
function(dom, request, on)
{
    var uri = "/rest/backup";
    var nextBackup = dom.byId("next");
    var lastBackup = dom.byId("last");

    var backupButton = dom.byId("backupButton");
    on(backupButton, "click", function() {
        request.post(uri, {
            sync: true,
            handleAs: "json",
            data: {}
        }).then (
            function(d) {
                nextBackup.innerHTML = d["next"];
                lastBackup.innerHTML = d["last"];
            },
            function(error) {
                console.log('[BACKUP] Communication Failure.');
            }
        );
    });
    

    var restoreButton = dom.byId("restoreButton");
    on(restoreButton, "click", function() {
        alert("restore");
    });

    request.get(uri, { handleAs: "json" }).then(
        function(d) {
            nextBackup.innerHTML = d["next"];
            lastBackup.innerHTML = d["last"];
        },
        function(error) {
            console.log('[BACKUP] Communication Failure.');
        }
    );

    return {}
});
