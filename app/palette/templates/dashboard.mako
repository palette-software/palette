# -*- coding: utf-8 -*-
<%inherit file="layout.mako" />

<%block name="title">
    <title>Palette - Home</title>
</%block>

<section class="secondary-side-bar">
    <a class="Psmall-only" id="toggle-events" href="#"><i class="fa"></i></a>
    <h5>Production</h5>
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
        <img src="/app/module/palette/images/server-icons-{{color}}.png" />
        <h5>{{displayname}}</h5>
        <p>{{ip_address}}</p>
      </a>
    </li>
    {{/agents}}
  </ul>
  {{/environments}}
</script>

<script src="/app/module/palette/js/vendor/require.js" data-main="/app/module/palette/js/dashboard.js">
</script>
