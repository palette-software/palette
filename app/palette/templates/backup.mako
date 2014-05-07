# -*- coding: utf-8 -*-
<%inherit file="layout.mako" />

<%block name="title">
    <title>Palette - Backup/Restore</title>
</%block>

<section class="secondary-side-bar">
    <a class="Psmall-only" id="toggle-events" href="#"><i class="fa fa-align-justify"></i><span> View Events</span></a>
    <ul class="actions">
        <li>
        	<a href="#"> 
        		<i class="fa fa-fw fa-download"></i>
        		<span>Backup</span>
        	</a>
        </li>
        <li>
        	<a href="#" class="inactive"> 
        		<i class="fa fa-fw fa-repeat"></i>
        		<span>Restore</span>
        	</a>
        </li>
    </ul>
    <h5 class="sub">Archive Backups to</h5>
    <div class="btn-group">
	  <button type="button" class="btn btn-default dropdown-toggle" data-toggle="dropdown"><div>Cloud Only</div><span class="caret"></span>
	  </button>
	  <ul class="dropdown-menu" role="menu">
	    <li><a href="#">Cloud Only</a></li>
	    <li><a href="#">Another action</a></li>
	    <li><a href="#">Something else here</a></li>
	  </ul>
	</div>
    <h5 class="sub">Produciton Backups</h5>
    <ul class="Logs">
        <li><a href="#"> 12:00 AM on Tuesday, March 11, 2014</a></li>
        <li><a href="#"> 12:00 AM on Tuesday, March 11, 2014</a></li>
        <li><a href="#"> 12:00 AM on Tuesday, March 11, 2014</a></li>
    </ul>
    <h5 class="sub">Staging Backups</h5>
    <ul class="Logs">
        <li><a href="#"> 12:00 AM on Tuesday, March 11, 2014</a></li>
        <li><a href="#"> 12:00 AM on Tuesday, March 11, 2014</a></li>
        <li><a href="#"> 12:00 AM on Tuesday, March 11, 2014</a></li>
    </ul>
</section>

<%include file="events.mako" />

<script src="/app/module/palette/js/vendor/require.js" data-main="/app/module/palette/js/common.js">

</script>
