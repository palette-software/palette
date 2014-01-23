define (["dojo/dom", "dojo/request", "dojo/domReady"],
function(dom, request)
{
    var status = dom.byId("status");

    function update() {
        request.get("/rest/monitor", { handleAs: "json" }).then(
            function(data) {
                status.innerHTML = data['status'];
            },
            function(error) {
                status.innerHTML = 'Communication Failure.';
            }
        );
    }

    update();
    var timer = setInterval(function() {
        update();
    }, 10000);

    return {}
});
