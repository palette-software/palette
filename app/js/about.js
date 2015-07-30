require(['jquery', 'topic', 'common', 'OnOff'],
function ($, topic, common, OnOff)
{
    /*
     * restartWebserver()
     */
    function restartWebserver() {        
        $.ajax({
            type: 'POST',
            url: '/rest/manage',
            data: {'action': 'restart-webserver'},
            dataType: 'json',
            async: false,
            
            success: function(data) {
                $('#restart-webserver').addClass('disabled');
            },
            error: common.ajaxError,
        });
    }

    /*
     * restartController()
     */
    function restartController() {
        $.ajax({
            type: 'POST',
            url: '/rest/manage',
            data: {'action': 'restart-controller'},
            dataType: 'json',
            async: false,
            
            success: function(data) {
                $('#restart-controller').addClass('disabled');

                /* If there are no agents connected, then there will be no
                 * state change - re-enabled the 'Restart Controller' button
                 * after a timeout regardless. */
                setTimeout(function () {
                    $('#restart-controller').removeClass('disabled');
                }, 10000);
            },
            error: common.ajaxError,
        });
    }

    /*
     * manualUpdate()
     */
    function manualUpdate() {
        $('#manual-update').addClass('disabled');
        $.ajax({
            type: 'POST',
            url: '/rest/manage',
            data: {'action': 'manual-update'},
            dataType: 'json',
            async: false,
            
            success: function(data) {
                update(data);
                $('#manual-update').removeClass('disabled');
            },
            error: common.ajaxError,
        });
    }

    /*
     * update()
     */
    function update(data) {
        $('#version').html(data['version']);
        $('#license-key').html(data['license-key']);
        OnOff.setValueById('enable-support', data['enable-support']);
        OnOff.setValueById('enable-updates', data['enable-updates']);
    }

    $.ajax({
        url: '/rest/about',
        dataType: 'json',
        
        success: function(data) {
            $().ready(function() {
                update(data);
                $('#manual-update').removeClass('disabled');
            });
        },
        error: common.ajaxError,
    });

    topic.subscribe('state', function(message, data) {
        if (data['connected']) {
            $('#restart-webserver').removeClass('disabled');
            $('#restart-controller').removeClass('disabled');
            $('#manual-update').removeClass('disabled');
        } else {
            $('#restart-webserver').addClass('disabled');
            $('#restart-controller').addClass('disabled');
            $('#manual-update').addClass('disabled');
        }
    });

    common.startMonitor(false);
    common.setupOkCancel();

    $().ready(function() {
        $('#restart-webserver').data('callback', restartWebserver);
        $('#restart-controller').data('callback', restartController);
        $('#manual-update').data('callback', manualUpdate);
        OnOff.setup();
    });
});
