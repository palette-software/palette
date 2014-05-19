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
      <a>
        <i class="fa fa-fw fa-hdd-o {{color}}"></i>
	    <div>
          <h5>{{displayname}}</h5>
          <span class="hostname">{{hostname}}</span>
          <span class="address">{{ip_address}}</span>
	    </div>
      </a>
      <ul class="processes">
	{{#details}}
	<li>
	  <a>
	    <i class="fa fa-fw fa-circle {{status}}"></i>
	    {{name}} ({{pid}})
	  </a>
	</li>
	{{/details}}
      </ul>
    </li>
    {{/agents}}
  </ul>
  {{/environments}}
</script>

<script src="/app/module/palette/js/vendor/require.js" data-main="/app/module/palette/js/dashboard.js">
</script>
