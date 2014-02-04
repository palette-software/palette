define (["dojo/dom", "dojo/request", "dojo/on",
         "dojox/widget/DialogSimple",
         "dojo/domReady"],
function(dom, request, on, DialogSimple)
{
    var uri = "/rest/manage";
    var diskspace = dom.byId("diskspace"); // temporary

    var startButton = dom.byId("startButton");
    on(startButton, "click", function() {
        request.post(uri, {
            sync: true,
            handleAs: "json",
            data: {"action": "start"}
        }).then (
            function(d) {
                diskspace.innerHTML = "START";
            },
            function(error) {
                console.log('[MANAGE] Communication Failure.');
            }
        );
    });
    

    var stopButton = dom.byId("stopButton");
    on(stopButton, "click", function() {
        request.post(uri, {
            sync: true,
            handleAs: "json",
            data: {"action": "stop"}
        }).then (
            function(d) {
                diskspace.innerHTML = "STOP";
            },
            function(error) {
                console.log('[MANAGE] Communication Failure.');
            }
        );
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
