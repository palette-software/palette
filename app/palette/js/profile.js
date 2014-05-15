require(['jquery', 'common', 'bootstrap', 'domReady!'],
function (jquery, common)
{

    function update(data) {
        var friendly = data['first-name'] + ' ' + data['last-name']
        jquery("#friendly").html(friendly);
        jquery("#email").html(data['email']);
        jquery("#username").html(data['name']);
        jquery("#user-license").html('Interactor');
        jquery("#user-administrator-role").html('System Administrator');
        jquery("#user-publisher-role").html('Publisher');
    }

    jquery.ajax({
        url: '/rest/profile',
        success: function(data) {
            update(data);
        },
        error: function(req, textStatus, errorThrown) {
            console.log('[ERROR] '+textStatus+': '+errorThrown);
        },
    });

    common.startup();
});
