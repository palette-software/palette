# -*- coding: utf-8 -*-
<%inherit file="layout.mako" />

<%block name="title">
    <title>Palette - Home</title>
</%block>

<div class="dashboard-page">

  <section class="top-zone">
    <div id="dashboard-type" class="dropdown-toggle btn-group"></div>
  </section>

  <div id="tableauViz"></div>
</div>

<script id="viz-template" type="x-tmpl-mustache">
  <div class='tableauPlaceholder' style='width: 100%;'>
    <object class='tableauViz' width='1200' height='900' style='display:none;'>
      <param name='host_url' value='https%3A%2F%2Fdemo-tableau.palette-software.com%2F' />
      <param name='site_root' value='' />
      <param name='name' value='{{id}}' />
      <param name='tabs' value='no' />
      <param name='toolbar' value='no' />
      <param name='showVizHome' value='n' />
    </object>
  </div>
</script>

<script src="/js/vendor/require.js" data-main="/js/dashboard.js">
</script>
