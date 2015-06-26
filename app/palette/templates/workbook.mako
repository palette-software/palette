# -*- coding: utf-8 -*-
<%inherit file="layout.mako" />

<%block name="title">
<title>Palette - Workbook Archive</title>
</%block>

<div class="dynamic-content workbook-page">
  <div class="scrollable">
    <section class="top-zone">
      <section class="row">
        <section class="col-xs-12">
          <%include file="paging.mako" args="name='Workbooks'" />
          <h1 class="page-title">Workbook Archive</h1>
        </section>
      </section>
      <section class="row">
        <section class="col-xs-12 filter-dropdowns">
          <div id="show-dropdown" class="dropdown-toggle btn-group"></div>
          <span>Sort by:</span>
          <div id="sort-dropdown" class="dropdown-toggle btn-group"></div>
          <span>Filter by:</span>
          <div id="site-dropdown" class="dropdown-toggle btn-group"></div>
	  <div id="project-dropdown" class="dropdown-toggle btn-group disabled"></div>
        </section>
      </section>
    </section>
    <section class="row bottom-zone">
      <section class="col-lg-12">
        <div id="workbook-list"></div>
      </section>
    </section>
  </div>
</div>

<script id="workbook-list-template" type="x-tmpl-mustache">
  {{#workbooks}}
  <article class="item">
    <div class="summary clearfix">
      <i class="fa fa-fw fa-book {{color}}"></i>
      <div>
        <div class="col2">
          <h3>{{name}}</h3>
          <p><span class="label">Publisher</span>{{last-updated-by}}</p>
        </div>
        <div class="col2">
          <div>
            <span class="label">Site</span>{{site}} and <span class="label">Project</span>{{project}}
          </div>
          <div>
            {{#url}}
            <a href="{{url}}">rev{{current-revision}} {{last-updated-at}}</a>
            {{/url}}
            {{^url}}
            rev{{current-revision}} {{last-updated-at}}
            {{/url}}
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
            {{#url}}
            <a href="{{url}}">rev{{revision}} {{timestamp}}</a> by {{username}}
            {{/url}}
            {{^url}}
            rev{{revision}} {{timestamp}} by {{username}}
            {{/url}}
          </div>
          <div>
            <span class="label">Note</span>
            <span class="editbox"
                  data-id="{{wuid}}"
                  data-href="/rest/workbooks/updates/note">
              {{note}}
            </span>
          </div>
        </li>
        {{/updates}}
      </ul>
    </div>
  </article>
  {{/workbooks}}
</script>

<script src="/js/vendor/require.js" data-main="/js/workbook.js">
</script>
