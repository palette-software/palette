# -*- coding: utf-8 -*-
<%inherit file="layout.mako" />

<%block name="title">
<title>Palette - Extracts</title>
</%block>

<section class="secondary-side-bar">
  <a class="Psmall-only" id="toggle-events" href="#"><i class="fa"></i></a>
  <h2>Filter</h2>
  <h5 class="sub margin-top">Extract</h5>
  <section class="padding">
    <input type="text" placeholder="Extract">
  </section>
  <h5 class="sub">Workbook</h5>
  <section class="padding">
    <input type="text" placeholder="Workbook">
  </section>
  <h5 class="sub">Publisher</h5>
  <div class="btn-group">
    <button type="button" class="btn btn-default dropdown-toggle" data-toggle="dropdown"><div>All Publishers</div><span class="caret"></span>
    </button>
    <ul class="dropdown-menu" role="menu">
      <li><a href="#">All Publishers</a></li>
      <li><a href="#">John Abdo</a></li>
      <li><a href="#">Matthew Laue</a></li>
    </ul>
  </div>
  <h5 class="sub">Project</h5>
  <div class="btn-group">
    <button type="button" class="btn btn-default dropdown-toggle" data-toggle="dropdown"><div>All Projects</div><span class="caret"></span>
    </button>
    <ul class="dropdown-menu" role="menu">
      <li><a href="#">All Projects</a></li>
      <li><a href="#">Quarterly Reports</a></li>
      <li><a href="#">Annual Reports</a></li>
    </ul>
  </div>
  <h5 class="sub">Datasource Type</h5>
  <div class="btn-group">
    <button type="button" class="btn btn-default dropdown-toggle" data-toggle="dropdown"><div>All Datasource Types</div><span class="caret"></span>
    </button>
    <ul class="dropdown-menu" role="menu">
      <li><a href="#">All Datasource Types</a></li>
      <li><a href="#">MySQL</a></li>
      <li><a href="#">Postgres</a></li>
      <li><a href="#">SQL Server</a></li>
    </ul>
  </div>
</section>

<section class="dynamic-content">
  <section class="top-zone">
    <section class="row">
      <section class="col-xs-12">
        <h1 class="page-title">Extracts</h1>
        <a class="Psmallish-only" id="toggle-event-filters" href="#"><i class="fa fa-angle-left"></i></a>
      </section>
    </section>
    <section class="row">
      <section class="col-xs-12">
        <div class="btn-group">
          <button type="button" class="btn btn-default dropdown-toggle" data-toggle="dropdown"><div>All Sites</div><span class="caret"></span>
          </button>
          <ul class="dropdown-menu" role="menu">
            <li><a href="#">All Sites</a></li>
            <li><a href="#">Finance</a></li>
            <li><a href="#">Marketing</a></li>
          </ul>
        </div>
	<div class="btn-group">
          <button type="button" class="btn btn-default dropdown-toggle" data-toggle="dropdown"><div>All Status</div><span class="caret"></span>
          </button>
          <ul class="dropdown-menu" role="menu">
            <li><a href="#">All Statuses</a></li>
            <li><a href="#">Success</a></li>
            <li><a href="#">Warning</a></li>
            <li><a href="#">Error</a></li>
          </ul>
        </div>
        <div class="btn-group pull-right">
          <button type="button" class="btn btn-default dropdown-toggle" data-toggle="dropdown"><i class="fa fa-fw fa-calendar"></i> Select Date<span class="caret"></span>
          </button>
          <ul class="dropdown-menu" role="menu">
            <li><a href="#">1 Week ago</a></li>
            <li><a href="#">2 Weeks ago</a></li>
            <li><a href="#">1 Month ago</a></li>
            <li><a href="#">2 Months ago</a></li>
            <li><a href="#">3 Months ago</a></li>
            <li><a href="#">6 Months ago</a></li>
          </ul>
        </div>
      </section>
    </section>
  </section>
  <section class="row bottom-zone">
    <section class="col-lg-12">
      <div id="extract-list"></div>
    </section>
  </section>
</section>

<%include file="servers.mako" />


<script id="extract-list-template" type="x-tmpl-mustache">
  {{#extracts}}
  <article class="event">
    <i class="fa fa-fw fa-copy {{color}}"></i>
    <h3>{{name}}</h3>
    <p>{{summary}}</p>
    <div>{{description}}</div>
  </article>
  {{/extracts}}
</script>

<script src="/app/module/palette/js/vendor/require.js" data-main="/app/module/palette/js/extracts.js">
</script>
