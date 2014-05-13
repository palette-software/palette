# -*- coding: utf-8 -*-
<%inherit file="layout.mako" />

<%block name="title">
<title>Palette - Workbook Archive</title>
</%block>

<section class="secondary-side-bar">
  <a class="Psmall-only" id="toggle-events" href="#"><i class="fa"></i></a>
  <h2>Filter</h2>
  <h5 class="sub margin-top">Workbook</h5>
  <section class="padding">
    <input type="text" placeholder="Workbook">
  </section>
  <h5 class="sub">Project</h5>
  <div class="btn-group">
    <button type="button" class="btn btn-default dropdown-toggle" data-toggle="dropdown"><div>All Projects</div><span class="caret"></span>
    </button>
    <ul class="dropdown-menu" role="menu">
      <li><a href="#">All Projects</a></li>
      <li><a href="#">Annual Reports</a></li>
      <li><a href="#">Quarterly Reports</a></li>
    </ul>
  </div>
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
</section>

<section class="dynamic-content">
  <section class="top-zone">
    <section class="row">
      <section class="col-xs-12">
        <h1 class="page-title">Workbook Archive</h1>
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
      </section>
    </section>
  </section>
  <section class="row bottom-zone">
    <section class="col-lg-12">
      <div id="workbook-list"></div>
    </section>
  </section>
</section>

<%include file="servers.mako" />

<script id="workbook-list-template" type="x-tmpl-mustache">
  {{#workbooks}}
  <article class="event">
    <i class="fa fa-fw fa-book {{color}}"></i>
    <h3>{{name}}</h3>
    <p>{{summary}}</p>
    <div>
      <ul>
         {{#updates}}
         <li>
	       <a href="#">{{timestamp}}</a> by {{name}}
           <a class="edit" href="#"><i class="fa fa-fw fa-pencil"></i></a>
	     </li>
         {{/updates}}
      </ul>
    </div>
  </article>
  {{/workbooks}}
</script>

<script src="/app/module/palette/js/vendor/require.js" data-main="/app/module/palette/js/workbook.js">
</script>
