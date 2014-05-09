# -*- coding: utf-8 -*-
<%inherit file="layout.mako" />

<%block name="title">
    <title>Palette - Extracts</title>
</%block>

<section class="secondary-side-bar">
    <a class="Psmall-only" id="toggle-events" href="#"><i class="fa"></i></a>
    <h5 class="sub margin-top">Extract Name</h5>
    <section class="padding">
    	<input type="text" placeholder="example">
    </section>
    <h5 class="sub">Publisher</h5>
    <div class="btn-group">
	  <button type="button" class="btn btn-default dropdown-toggle" data-toggle="dropdown"><div>First Publisher</div><span class="caret"></span>
	  </button>
	  <ul class="dropdown-menu" role="menu">
	    <li><a href="#">First Publisher</a></li>
	    <li><a href="#">Another action</a></li>
	    <li><a href="#">Something else here</a></li>
	  </ul>
	</div>
	<h5 class="sub">Project</h5>
    <div class="btn-group">
	  <button type="button" class="btn btn-default dropdown-toggle" data-toggle="dropdown"><div>First Project</div><span class="caret"></span>
	  </button>
	  <ul class="dropdown-menu" role="menu">
	    <li><a href="#">Cloud Only</a></li>
	    <li><a href="#">Another action</a></li>
	    <li><a href="#">Something else here</a></li>
	  </ul>
	</div>
	<h5 class="sub">Site</h5>
    <div class="btn-group">
	  <button type="button" class="btn btn-default dropdown-toggle" data-toggle="dropdown"><div>First Site</div><span class="caret"></span>
	  </button>
	  <ul class="dropdown-menu" role="menu">
	    <li><a href="#">Cloud Only</a></li>
	    <li><a href="#">Another action</a></li>
	    <li><a href="#">Something else here</a></li>
	  </ul>
	</div>
	<h5 class="sub">Status</h5>
    <div class="btn-group">
	  <button type="button" class="btn btn-default dropdown-toggle" data-toggle="dropdown"><div>Type</div><span class="caret"></span>
	  </button>
	  <ul class="dropdown-menu" role="menu">
	    <li><a href="#">All</a></li>
	    <li><a href="#">Success</a></li>
	    <li><a href="#">Failure</a></li>
	    <li><a href="#">Pending</a></li>
	  </ul>
	</div>
</section>

<%include file="events.mako" />

<script src="/app/module/palette/js/vendor/require.js" data-main="/app/module/palette/js/common.js">

</script>
