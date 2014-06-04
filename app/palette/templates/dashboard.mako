# -*- coding: utf-8 -*-
<%inherit file="layout.mako" />

<%block name="title">
    <title>Palette - Home</title>
</%block>

<section class="dynamic-content">
    <%include file="events.mako" />
</section>

<script src="/app/module/palette/js/vendor/require.js" data-main="/app/module/palette/js/dashboard.js">
</script>
