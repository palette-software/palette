# -*- coding: utf-8 -*-
<%inherit file="webapp.mako" />

<%block name="title">
<title>Palette - Data Source Archive</title>
</%block>

<div class="content datasource-page">
  <div>
    <div class="top-zone">
      <%include file="paging.mako" args="name='Data Sources'" />
      <h1>Data Source Archive</h1>
      <div class="filter-dropdowns">
        <div id="show-dropdown" class="btn-group"></div>
        <span>Sort by:</span>
        <div id="sort-dropdown" class="btn-group"></div>
        <span>Filter by:</span>
        <div id="site-dropdown" class="btn-group"></div>
        <div id="project-dropdown" class="btn-group disabled"></div>
      </div>
    </div> <!-- top-zone -->
    <div class="bottom-zone">
      <div id="datasource-list">
        <div class="empty-message hidden admin-only">
          <p>The Palette Data Source Archive can only be imported if the Palette Agent has been properly installed on your Tableau Machine(s) <em>and</em> if you have input your Tableau Server administrator credentials into the Configuration -> General page.</p>
          <p>If you have not yet installed the Palette Agent, please visit <a href="http://www.palette-software.com/agent">palette-software.com/agent</a> from your Tableau Server machines to get connected!</p>
        </div>
        <div class="empty-message hidden publisher-only">
          <p>Your personal Palette Data Source Archive will begin to import when a Tableau Server administrator inputs their credentials.  Please contact your Tableau Server admin to tell them you'd like to access this feature.
          </p>
        </div>
      </div>
    </div> <!-- bottom-zone -->
  </div>
</div> <!-- content -->

<script id="datasource-list-template" type="x-tmpl-mustache">
  {{#datasources}}
  <article class="item">
    <div class="summary clearfix" data-toggle="item">
      <i class="data-source {{color}}"></i>
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
      <i class="expand"></i>
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
                  data-id="{{dsid}}"
                  data-href="/rest/datasources/updates/note">
              {{note}}
            </span>
          </div>
        </li>
        {{/updates}}
      </ul>
    </div>
  </article>
  {{/datasources}}
</script>

<script src="/js/vendor/require.js" data-main="/js/datasource.js">
</script>
