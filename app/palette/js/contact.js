function loadUserVoice() {
    var uv=document.createElement('script');
    uv.type='text/javascript';
    uv.async=true;
    uv.src='//widget.uservoice.com/lkdy4cXMROT7BNOEJZ9G1g.js';
    var s=document.getElementsByTagName('script')[0];
    s.parentNode.insertBefore(uv,s)
}

function showClassicWidget() {
    loadUserVoice();

    UserVoice = window.UserVoice || [];
    UserVoice.push(['showLightbox', 'classic_widget', {
        mode: 'support',
        primary_color: '#333333',
        link_color: '#5f6670',
        default_mode: 'support',
        forum_id: 258262
    }]);
}
