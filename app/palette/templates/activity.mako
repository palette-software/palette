# -*- coding: utf-8 -*-
<%inherit file="layout.mako" />

<%block name="title">
    <title>Palette - Activity</title>
</%block>

<section class="secondary-side-bar">
    <a class="Psmall-only" id="toggle-events" href="#"><i class="fa fa-align-justify"></i><span> View Events</span></a>
    <h5 class="sub margin-top">Example</h5>
    <section class="padding">
    	<input type="text" placeholder="example">
    </section>
    <h5 class="sub">Placeholder</h5>
    <div class="btn-group">
	  <button type="button" class="btn btn-default dropdown-toggle" data-toggle="dropdown"> Placeholder<span class="caret"></span>
	  </button>
	  <ul class="dropdown-menu" role="menu">
	    <li><a href="#">Example</a></li>
	    <li><a href="#">Another action</a></li>
	    <li><a href="#">Something else here</a></li>
	  </ul>
	</div>
    <h5 class="sub">Placeholder</h5>
    <div class="btn-group">
	  <button type="button" class="btn btn-default dropdown-toggle" data-toggle="dropdown"> Placeholder<span class="caret"></span>
	  </button>
	  <ul class="dropdown-menu" role="menu">
	    <li><a href="#">Example</a></li>
	    <li><a href="#">Another action</a></li>
	    <li><a href="#">Something else here</a></li>
	  </ul>
	</div>
</section>

<%include file="events.mako" />

<script src="/app/module/palette/js/vendor/require.js" data-main="/app/module/palette/js/common.js">

</script>
