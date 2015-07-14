# -*- coding: utf-8 -*-
<%inherit file="layout.mako" />

<%block name="title">
    <title>Palette - Events</title>
</%block>

<div class="dynamic-content">
  <%include file="events.mako" />
</div>

<script src="/js/vendor/require.js" data-main="/js/events.js">
</script>
