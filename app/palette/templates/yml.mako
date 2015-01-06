# -*- coding: utf-8 -*-
<%inherit file="layout.mako" />

<%block name="title">
<title>Palette - Tableau Settings</title>
</%block>

<div class="dynamic-content configuration">
  <div class="scrollable">
    <h1 class="page-title">Tableau Settings</h1>
    <div class="refresh">
      <p>
        Updated <span id="last-update"></span>
      </p>
      <p id="location"></p>
    </div>
    <div id="yml-list"></div>
  </div>
</div>

<script id="yml-list-template" type="x-tmpl-mustache">
  {{#items}}
  <section class="row">
    <section class="col-md-4 key">
      {{key}}
    </section>
    <section class="col-md-6">
      {{value}}
    </section>
  </section>
  {{/items}}
</script>

<script src="/app/module/palette/js/vendor/require.js" data-main="/app/module/palette/js/yml.js">
</script>
