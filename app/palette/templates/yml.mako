# -*- coding: utf-8 -*-
<%inherit file="webapp.mako" />

<%block name="title">
<title>Palette - Tableau Settings</title>
</%block>

<div class="dynamic-content">
  <div class="scrollable">
    <div class="top-zone">
      <div class="refresh">
        <p>Updated <span id="last-update"></span></p>
        <p id="location"></p>
      </div>
      <h1>Tableau&nbsp;Settings</h1>
    </div> <!-- top-zone -->
    <div class="bottom-zone">
      <div id="yml-list">
	<%include file="empty.mako" />
      </div>
    </div>
  </div>
</div>

<script id="yml-list-template" type="x-tmpl-mustache">
  {{#items}}
  <div class="row">
    <div class="col-md-4 key">
      {{key}}
    </div>
    <div class="col-md-6">
      {{value}}
    </div>
  </div>
  {{/items}}
</script>

<script src="/js/vendor/require.js" data-main="/js/yml.js">
</script>
