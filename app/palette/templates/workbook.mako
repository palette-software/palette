# -*- coding: utf-8 -*-
<%inherit file="layout.mako" />

<%block name="title">
<title>Palette - Workbook Archive</title>
</%block>

<section class="dynamic-content workbook-page">
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
	<div class="col2">
          <h3>{{name}}</h3>
          <p><span class="label">Current Publisher</span>{{last-updated-by}}</p>
	</div>
	<div class="col2">
          <div>
	    <span class="label">Site</span>{{site}} and <span class="label">Project</span>{{project}}
	  </div>
          <div>
	    <span class="label">Last Updated</span><a href="{{url}}">{{last-updated-at}}</a>
	  </div>
        </div>
      </div>
      <i class="fa fa-fw fa-angle-down expand"></i>
    </div>
    <div class="description">
      <ul>
        {{#updates}}
        <li>
          <div>
	    <a href="{{url}}">rev{{revision}} {{timestamp}}</a> by {{username}}
	  </div>
	  <div>
	    <span class="label">Note</span>
	    <span class="editbox"
		  data-id="{{wuid}}"
		  data-href="/rest/workbooks/updates/note">
	    </span>
	  </div>
        </li>
        {{/updates}}
      </ul>
    </div>
  </article>
  {{/workbooks}}
</script>

<script src="/app/module/palette/js/vendor/require.js" data-main="/app/module/palette/js/workbook.js">
</script>
