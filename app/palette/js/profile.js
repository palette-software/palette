require.config({
    paths: {
        'jquery': '/app/module/palette/js/vendor/jquery',
    }
});

require(['jquery', 'common'],
function (jquery)
{

    function update(data) {
        var friendly = data['first-name'] + ' ' + data['last-name']
        jquery("input[name='friendly']").val(friendly);
        jquery("input[name='email']").val(data['email']);
        jquery("input[name='username']").val(data['name']);
        jquery("input[name='user-license']").val('Interactor');
        jquery("input[name='user-administrator-role']").val('System Administrator');
        jquery("input[name='user-publisher-role']").val('Publisher');
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
});
