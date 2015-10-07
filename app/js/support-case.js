require(['jquery', 'common', 'Dropdown'],
function ($, common, Dropdown
)
{
    var URL = '/rest/support-case';

    function gather() {
        var data = {}

        $('input[type=text], textarea').each(function(index){
            var id = $(this).attr('id');
            data[id] = $('#' + id).val();
        });
        return data;
    }

    /*
     * sendSupportCase()
     */
    function sendSupportCase() {
        $('#send-support-case').addClass('disabled');
        $.ajax({
            type: 'POST',
            url: URL,
            data: gather(),
            dataType: 'json',
            
            success: function(data) {
                $('#send-support-case').removeClass('disabled');
                $('#okcancel').removeClass('visible');
            },
            error: function(jqXHR, textStatus, errorThrown) {
                common.ajaxError(jqXHR, textStatus, errorThrown);
                $('#okcancel').removeClass('visible');
            }
        });
    }

    common.startMonitor(false);
    common.setupOkCancel();

    $.ajax({
        url: URL,
        dataType: 'json',
        
        success: function(data) {
            $().ready(function() {
                Dropdown.setupAll(data);
                $('#send-support-case').data('callback', sendSupportCase);
                $('#send-support-case').removeClass('disabled');
            });
        },
        error: common.ajaxError,
    });
});
