require.config({
    paths: {
        'jquery': '/app/module/palette/js/vendor/jquery',
    }
});

require(['jquery', 'common'],
function (jquery)
{

    function update(data) {
        jquery("input[name='firstname']").val(data['first-name']);
        jquery("input[name='lastname']").val(data['last-name']);
        jquery("input[name='email']").val(data['email']);
        jquery("input[name='username']").val(data['name']);
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
