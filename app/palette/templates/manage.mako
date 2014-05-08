# -*- coding: utf-8 -*-
<%inherit file="layout.mako" />

<%block name="title">
    <title>Palette - Manage</title>
</%block>

<section class="secondary-side-bar">
    <a class="Psmall-only" id="toggle-events" href="#"><i class="fa"></i></a>
    <h5>Tableau Server Application</h5>
    <h5 class="sub">123.123.1.1</h5>
    <h5 class="sub">Port 6577</h5>
    <ul class="actions">
        <li>
        	<a href="#"> 
        		<i class="fa fa-fw fa-play"></i>
        		<span>Start</span>
        	</a>
        </li>
        <li>
        	<a href="#"> 
        		<i class="fa fa-fw fa-stop"></i>
        		<span>Stop</span>
        	</a>
        </li>
        <li>
        	<a href="#"> 
        		<i class="fa fa-fw fa-repeat"></i>
        		<span>Reset</span>
        	</a>
        </li>
        <li>
        	<a href="#"> 
        		<i class="fa fa-fw fa-power-off"></i>
        		<span>Restart Server</span>
        	</a>
        </li>
    </ul>
</section>

<%include file="events.mako" />

<script src="/app/module/palette/js/vendor/require.js" data-main="/app/module/palette/js/common.js">
</script>
