# -*- coding: utf-8 -*-
<%inherit file="layout.mako" />

<%block name="title">
<title>Palette - Logs</title>
</%block>

<section class="secondary-side-bar">
  <h2>Actions</h2>
  <ul class="actions">
    <li>
      <a href="#"><i class="fa fa-fw fa-list"></i>Make Logs</a>
    </li>
  </ul>

  <h5 class="logs-page">Log Archive Location</h5>
  <div class="btn-group dropdown">
    <button type="button" class="btn btn-default dropdown-toggle"
            data-toggle="dropdown"><div>Palette Cloud Storage</div><span class="caret"></span>
    </button>
    <ul class="dropdown-menu" role="menu">
      <li><a href="#">Palette Cloud Storage</a></li>
      <li><a href="#">On-Premise Storage</a></li>
    </ul>
  </div>

  <h5 class="logs-page">Log History</h5>
  <ul class="Logs">
    <li><a href="#"> 12:00 AM PDT on May 6, 2014</a></li>
    <li><a href="#"> 12:00 AM PDT on April 1, 2014</a></li>
    <li><a href="#"> 12:00 AM PDT on March 11, 2014</a></li>
  </ul>
</section>

<%include file="events.mako" />

<script src="/app/module/palette/js/vendor/require.js" data-main="/app/module/palette/js/logs.js">
</script>
