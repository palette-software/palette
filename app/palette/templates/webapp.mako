# -*- coding: utf-8 -*-
<%inherit file="layout.mako" />

<body>
<%include file="mainnav.mako" />

<div class="container-fluid">

<%include file="side-bar.mako" />

<section class="secondary-side-bar servers">
  <div id="server-list"></div>
</section>

${next.body()}
</div>

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
  <i class="fa fa-fw fa-check ok"></i>
  <i class="fa fa-fw fa-times cancel"></i>
</script>

<article class="popup" id="okcancel">
  <section class="popup-body">
    <section class="row">
      <section class="col-xs-12">
        <p>&nbsp;</p>
      </section>
    </section>
    <section class="row">
      <section class="col-xs-6">
        <button class="p-btn popup-ok">OK</button>
      </section>
      <section class="col-xs-6">
        <button class="p-btn popup-close">Cancel</button>
      </section>
    </section>
  </section>
  <div class="shade">&nbsp;</div>
</article>

<%include file="dropdown.mako" />
<%include file="onoff.mako" />

</body>
