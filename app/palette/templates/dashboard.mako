# -*- coding: utf-8 -*-
<%inherit file="layout.mako" />

<%block name="title">
    <title>Palette - Home</title>
</%block>

<section class="secondary-side-bar">
    <a class="Psmall-only" id="toggle-events" href="#"><i class="fa"></i></a>
    <div id="server-list"></div>
</section>

<%include file="events.mako" />

<script id="server-list-template" type="x-tmpl-mustache">
  {{#environments}}
  <h5>{{name}}</h5>
  <ul class="server-list">
    {{#agents}}
    <li>
      <a href="#">
        <i class="fa fa-fw fa-hdd-o {{color}}"></i>
        <h5>{{displayname}}</h5>
        <span class="hostname">{{hostname}}</span>
        <span class="address">{{ip_address}}</span>
      </a>
    </li>
    {{/agents}}
  </ul>
  {{/environments}}
</script>

<script src="/app/module/palette/js/vendor/require.js" data-main="/app/module/palette/js/dashboard.js">
</script>
