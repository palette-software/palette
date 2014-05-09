# -*- coding: utf-8 -*-
<%inherit file="layout.mako" />

<%block name="title">
<title>Palette - Manage</title>
</%block>

<section class="secondary-side-bar">
  <a class="Psmall-only" id="toggle-events" href="#"><i class="fa"></i></a>
  <h5>Tableau Server Application</h5>
  <h5 class="sub">X.X.X.X</h5>
  <h5 class="sub">Port XXXX</h5>
  <ul class="actions">
    <li>
      <a href="#" id="start" class="inactive">
        <i class="fa fa-fw fa-play"></i>
        <span>Start</span>
      </a>
    </li>
    <li>
      <a href="#" id="stop" class="inactive"> 
        <i class="fa fa-fw fa-stop"></i>
        <span>Stop</span>
      </a>
    </li>
    <li>
      <a href="#" id="reset" class="inactive"> 
        <i class="fa fa-fw fa-repeat"></i>
        <span>Reset</span>
      </a>
    </li>
    <li>
      <a href="#" id="restart" class="inactive"> 
        <i class="fa fa-fw fa-power-off"></i>
        <span>Restart Server</span>
      </a>
    </li>
  </ul>
</section>

<%include file="events.mako" />

<script src="/app/module/palette/js/vendor/require.js" data-main="/app/module/palette/js/manage.js">
</script>
