# -*- coding: utf-8 -*-
<%inherit file="layout.mako" />

<%block name="title">
    <title>Palette - Activities</title>
</%block>

<section class="secondary-side-bar">
    <a class="Psmall-only" id="toggle-events" href="#"><i class="fa fa-align-justify"></i><span> View Events</span></a>
    <h5><i class="fa fa-fw fa-archive"></i> Archive Logs</h5>
    <h5 class="sub">Log History</h5>
    <ul class="Logs">
        <li><a href="#"> 12:00 AM on Tuesday, March 11, 2014</a></li>
        <li><a href="#"> 12:00 AM on Tuesday, March 11, 2014</a></li>
        <li><a href="#"> 12:00 AM on Tuesday, March 11, 2014</a></li>
    </ul>
</section>

<%include file="events.mako" />

<script src="/app/module/palette/js/vendor/require.js" data-main="/app/module/palette/js/common.js">
</script>

</script>
