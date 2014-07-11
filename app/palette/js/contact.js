function loadUserVoice() {
    var uv=document.createElement('script');
    uv.type='text/javascript';
    uv.async=true;
    uv.src='//widget.uservoice.com/OggeFPvaqWHCBdmBclbA.js';
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
        support_tab_name: 'Contact Palette',
        forum_id: 253967
    }]);
}
