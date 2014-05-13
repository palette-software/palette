# -*- coding: utf-8 -*-
<%inherit file="layout.mako" />

<%block name="title">
    <title>Palette - Home</title>
</%block>

<section class="secondary-side-bar servers">
  <a class="Psmall-only" id="toggle-events" href="#"><i class="fa"></i></a>
  <div id="server-list"></div>
</section>


<section class="home-events">
    <%include file="events.mako" />
</section>

<script id="server-list-template" type="x-tmpl-mustache">
  {{#environments}}
  <h2>{{name}}</h2>
  <ul class="server-list">
    {{#agents}}
    <li>
      <a href="#">
        <i class="fa fa-fw fa-hdd-o {{color}}"></i>
	    <div>
          <h5>{{displayname}}</h5>
          <span class="hostname">{{hostname}}</span>
          <span class="address">{{ip_address}}</span>
	    </div>
      </a>
      <ul class="processes">
        <li><a href="#"><i class="fa fa-fw fa-circle running"></i>Repository Database (296) is running.</a></li>
        <li><a href="#"><i class="fa fa-fw fa-circle running"></i>Search Service (1512) is running.</a></li>
        <li><a href="#"><i class="fa fa-fw fa-circle running"></i>Data Engine Extract 0 (844) is running.</a></li>
        <li><a href="#"><i class="fa fa-fw fa-circle running"></i>Vizqlserver 0 (1612) is running.</a></li>
        <li><a href="#"><i class="fa fa-fw fa-circle running"></i>Vizqlserver 1 (764) is running.</a></li>
        <li><a href="#"><i class="fa fa-fw fa-circle running"></i>Backgrounder 0 (2052) is running.</a></li>
        <li><a href="#"><i class="fa fa-fw fa-circle running"></i>Dataserver 0 (2060) is running.</a></li>
        <li><a href="#"><i class="fa fa-fw fa-circle running"></i>Dataserver 1 (2068) is running.</a></li>
        <li><a href="#"><i class="fa fa-fw fa-circle running"></i>Web Application 0 (2076) is running.</a></li>
        <li><a href="#"><i class="fa fa-fw fa-circle running"></i>Web Application 1 (2084) is running.</a></li>
        <li><a href="#"><i class="fa fa-fw fa-circle running"></i>Gateway (2100) is running.</a></li>
      </ul>
    </li>
    {{/agents}}
  </ul>
  {{/environments}}
</script>

<script src="/app/module/palette/js/vendor/require.js" data-main="/app/module/palette/js/dashboard.js">
</script>
