# -*- coding: utf-8 -*- 
<%inherit file="layout.mako" />

<%block name="title">
<title>Palette - Activities </title>
</%block>

<script src="/app/module/palette/js/vendor/require.js"
        data-main="/app/module/palette/js/dashboard.js" >
</script>

<%include file="side-bar.mako" />

<section class="secondary-side-bar">
  <h5>Production</h5>
  <ul class="server-list">
    <li>
      <a href="#">
        <img src="/app/module/palette/images/server-icons-green.png">
        <h5>Tableau Server Worker</h5>
        <p>123.123.1.2</p>
      </a>
    </li>
    <li>
      <a href="#">
        <img src="/app/module/palette/images/server-icons-green.png">
        <h5>Tableau Server Worker</h5>
        <p>123.123.1.2</p>
      </a>
    </li>
    <li>
      <a href="#">
        <img src="/app/module/palette/images/server-icons-green.png">
        <h5>Tableau Server Worker</h5>
        <p>123.123.1.2</p>
      </a>
    </li>
  </ul>
</section>
<%include file="events.mako" />

