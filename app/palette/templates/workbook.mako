# -*- coding: utf-8 -*-
<%inherit file="layout.mako" />

<%block name="title">
<title>Palette - Workbook Archive</title>
</%block>

<section class="secondary-side-bar">
  <h2>Filter</h2>
  <h5 class="sub margin-top">Workbook</h5>
  <section class="padding">
    <input type="text" placeholder="Workbook">
  </section>
  <h5 class="sub">Project</h5>
  <div class="btn-group">
    <button type="button" class="btn btn-default dropdown-toggle" data-toggle="dropdown">
      <div>All Projects</div>
      <span class="caret"></span>
    </button>
    <ul class="dropdown-menu" role="menu">
      <li><a href="#">All Projects</a></li>
    </ul>
  </div>
  <h5 class="sub">Publisher</h5>
  <div class="btn-group">
    <button type="button" class="btn btn-default dropdown-toggle" data-toggle="dropdown"><div>All Publishers</div><span class="caret"></span>
    </button>
    <ul class="dropdown-menu" role="menu">
      <li><a href="#">All Publishers</a></li>
    </ul>
  </div>
</section>

<section class="dynamic-content with-secondary-sidebar">
  <section class="top-zone">
    <section class="row">
      <section class="col-xs-12">
        <h1 class="page-title">Workbook Archive</h1>
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

<script id="workbook-list-template" type="x-tmpl-mustache">
  {{#workbooks}}
  <article class="event">
    <div class="summary clearfix">
      <i class="fa fa-fw fa-book {{color}}"></i>
      <div>
        <h3>{{name}}</h3>
        <p>{{summary}}</p>
      </div>
      <i class="fa fa-fw fa-angle-down expand"></i>
    </div>
    <div class="description">
      <ul>
        {{#updates}}
        <li>
          <a href="#">{{timestamp}}</a> by {{username}}
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


