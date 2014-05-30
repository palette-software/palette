# -*- coding: utf-8 -*-
<%inherit file="layout.mako" />

<%block name="title">
<title>Palette - Server Configuration</title>
</%block>

<section class="dynamic-content">
  <h1 class="page-title">Servers</h1>
  <section class="bottom-zone">
    <div id="server-list"></div>
  </section>
</section>

<script id="server-list-template" type="x-tmpl-mustache">
  {{#servers}}
  <article class="event">
    <div class="summary clearfix">
      <i class="fa fa-fw fa-user"></i>
      <div class="col-md-5">
	<h3>{{displayname}}</h3>
	<p>FQDN ({{ip-address}})</p>
      </div>
      <div class="col-md-5">
	<p>Environment {{environment}}</p>
	<p>Connection Status {{connection-status}}</p>
      </div>
      <i class="fa fa-fw fa-angle-down expand"></i>
    </div>
    <div class="description clearfix">
      <div class="col-md-5">
        <article><span class="label">Server Type</span>{{server-type}}</article>
	<br/>
        <article>
          <span class="label">Hostname</span>{{hostname}}
        </article>
        <article><span class="label">IP Address</span>{{ip-address}}</article>
        <article><span class="label">Environment</span>{{environment}}</article>
        <article><span class="label">OS</span>{{os}}</article>
        <article><span class="label">RAM</span>{{ram-mb}}</article>
	<article><span class="label">CPU Cores</span>{{cpu-cores}}</article>
	<br/>
      </div>
      <div class="col-md-5">
        <article>
          <span class="label">Select Archive Locations</span>
        </article>
      </div>
    </div>
  </article>
  {{/servers}}
</script>

<script src="/app/module/palette/js/vendor/require.js" data-main="/app/module/palette/js/servers.js">
</script>
