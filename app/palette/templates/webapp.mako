# -*- coding: utf-8 -*-
<%inherit file="layout.mako" />

<body>
<%include file="navbar.mako" />

<div class="container-webapp">

<%include file="side-bar.mako" />

<section class="secondary-side-bar servers-side-bar">
  <div id="server-list">
    <h1>My Machines</h1>
    <p>Palette cannot connect to your Tableau Machine.</p>
    <p>Please Install a <a href="http://www.palette-software.com/agent">Palette Agent</a> on your Tableau Machine.
  </div>
</section>

${next.body()}

</div> <!-- container-webapp -->

<script id="server-list-template" type="x-tmpl-mustache">
  {{#environments}}
  <h1>{{name}}</h1>
  <ul class="server-list">
    {{#agents}}
    <li>
      <a>
        <i class="fa fa-fw fa-laptop {{color}}"></i>
            <div>
          <h5>{{displayname}}</h5>
          <span class="hostname">{{hostname}}</span>
          <span class="address">{{ip_address}}</span>
            </div>
        <i class="fa fa-fw fa-angle-down down-arrow"></i>
      </a>
      <ul class="processes {{visible}}">
        {{#volumes}}
        <li>
          <i class="fa fa-fw fa-circle {{color}}"></i>
          Storage: {{name}} {{value}}
        </li>
        {{/volumes}}
        {{#cpu}}
        <li>
          <i class="fa fa-fw fa-circle {{color}}"></i>
          CPU
        </li>
        {{/cpu}}
        {{#license}}
        <li>
          <i class="fa fa-fw fa-circle {{color}}"></i>
          License: Tableau
        </li>
        {{/license}}
        {{#in_ports}}
        <li>
           <i class="fa fa-fw fa-circle {{color}}"></i>
           NETin: {{name}} ({{num}})
        </li>
        {{/in_ports}}
        {{#out_ports}}
        <li>
           <i class="fa fa-fw fa-circle {{color}}"></i>
           NETout: {{name}} ({{num}})
        </li>
        {{/out_ports}}
        {{#details}}
        <li>
          <i class="fa fa-fw fa-circle {{color}}"></i>
          {{name}} ({{pid}})
        </li>
        {{/details}}
        {{#warnings}}
        <li>
          <i class="fa fa-fw fa-circle {{color}}"></i>
          {{message}}
        </li>
        {{/warnings}}
      </ul>
    </li>
    {{/agents}}
  </ul>
  {{/environments}}
</script>

<script id="editbox-view" type="x-tmpl-mustache">
  <span>{{value}}</span>
  <i class="fa fa-fw fa-pencil"></i>
</script>

<script id="editbox-edit" type="x-tmpl-mustache">
  <input type="text" value="{{value}}" />
  <i class="fa fa-fw fa-times cancel"></i>
  <i class="fa fa-fw fa-check ok"></i>
</script>

<article class="popup" id="okcancel">
  <section class="popup-body">
    <div>
      <p>Are you sure you want to continue?</p>
    </div>
    <div>
      <button class="cancel">Cancel</button>
      <button class="ok">OK</button>
    </div>
  </section>
  <div class="shade">&nbsp;</div>
</article>

<%block name="popups">
</%block>

<%include file="dropdown.mako" />
<%include file="onoff.mako" />

</body>
