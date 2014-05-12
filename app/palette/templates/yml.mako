# -*- coding: utf-8 -*-
<%inherit file="configure.mako" />

<%block name="title">
<title>Palette - Tableau Settings</title>
</%block>

<section class="dynamic-content config-content">
  <section class="top-zone">
    <h1 class="page-title">Tableu Settings</h1>
  </section>
  <section class="bottom-zone">
    <div id="yml-list"></div>
  </section>
</section>

<script id="yml-list-template" type="x-tmpl-mustache">
  {{#items}}
  <section class="row">
    <section class="col-md-6 key">
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
