# -*- coding: utf-8 -*- 
<%inherit file="_layout.mako" />

<%block name="title">
<title>Palette</title>
</%block>

<%block name="favicon">
<%include file="favicon.mako" />
</%block>

<%block name="style">
<meta charset="utf-8">
<meta name="viewport" content="initial-scale=1, maximum-scale=1, user-scalable=no, width=device-width">
<link href="http://fonts.googleapis.com/css?family=Roboto:300,400,700|Lato:100,300,400" rel="stylesheet" type="text/css">
<link rel="stylesheet" type="text/css" href="/app/module/palette/css/style.css" media="screen">
<link rel="stylesheet" type="text/css" href="/app/module/palette/css/foundation.css">
<link rel="stylesheet" type="text/css" href="/app/module/palette/css/foundation-icons.css">
<link rel="stylesheet" type="text/css" href="/app/module/palette/css/new-style.css">
<script src="/app/module/palette/js/vendor/modernizr.js"></script>
</%block>

<h1>Palette Software</h1>
<div class="row dashboard">
  <div class="large-12 columns">
    <div class="row">
      <div class="large-6 medium-6 small-12 xsmall-12 columns">
        <section class="tile-module">
          <div class="panel-body">
            <div class="title">System Monitor</div>
            <div id="green" class="green-light" style="display:none"></div>
            <div id="yellow" class="yellow-light" style="display:none"></div>
            <div id="orange" class="orange-light" style="display:none"></div>
            <div id="red" class="red-light" style="display:none"></div>
            <p id="status-message" class="large"></p>
            <p class="tile-advanced">
              <a id="advanced-status" href="#"><span class="fi-list"></span></a>
            </p>
          </div>
        </section>
      </div>

      <div class="large-6 medium-6 small-12 xsmall-12 columns">
        <section class="tile-module">
          <div class="panel-body">
            <div class="title">Backup</div>
            <h3>Last</h3>
            <p id="last">— — — —</p>
            <h3>Next</h3>
            <p id="next">${obj.next}</p>
            <ul class="small-block-grid-2">
              <li><a id="backupButton" class="tile-button"><span class="fi-download"></span><p>Backup</p></a></li>
              <li><a id="restoreButton" class="tile-button"><span class="fi-arrow-left"></span><p>Restore</p></a></li>
            </ul>
            <p class="tile-advanced">
              <a id="advanced-backup" href="#"><span class="fi-list"></span></a>
            </p>
          </div>
        </section>
      </div>
    </div>
    <div class="row">
      <div class="large-6 medium-6 small-12 xsmall-12 columns">
        <section class="tile-module">
          <div class="panel-body">
            <div class="title">Tableau Support Case Builder</div>
            <ul class="small-block-grid-1">
              <li>&nbsp;</li>
              <li><a href="#" class="tile-button"><span class="fi-check"></span><p>Submit</p></a></li>
              <li>&nbsp;</li>
            </ul>
            <p class="tile-advanced">
              <a href="#"><span class="fi-list"></span></a>
            </p>
          </div>
        </section>
      </div>

      <div class="large-6 medium-6 small-12 xsmall-12 columns">
        <section class="tile-module vertical-center">
          <div class="panel-body">
            <div class="title">Manage Tableau Server</div>
            <ul class=" small-block-grid-2">
              <li>&nbsp;</li>
              <li>&nbsp;</li>
              <li><a id="startButton" href="#" class="tile-button"><span class="fi-play"></span><p>Start</p></a></li>
              <li><a id="stopButton" href="#" class="tile-button"><span class="fi-stop"></span><p>Stop</p></a></li>
              <li>&nbsp;</li>
              <li>&nbsp;</li>
            </ul>
            <p id="diskspace" class= large"></p>
            <p class="tile-advanced">
              <a id="advanced-manage" href="#"><span class="fi-list"></span></a>
            </p>
          </div>
        </section>
      </div>
    </div>
  </div>
</div>
    <!--
    <div class="tile">
      <h2 class="bottomRow">Manage Tableau Server</h2>
      <p class="pad">
        <a id="startButton" href="#" class="button spacer disabled">Start</a>
        <a id="stopButton" href="#" class="button">Stop</a>
      </p>
      <p id="diskspace" class="large"></p>
      <p class="tile-advanced">
        <a id="advanced-manage" href="#"><span class="fi-list"></span></a>
      </p>
    </div>
  </div>
</div>-->

<script>
require({
  packages: [
    { name: "palette", location: "/app/module/palette/js" }
  ]
}, [ "palette/monitor", "palette/backup", "palette/manage" ]);
</script>

<script src="/app/module/palette/js/vendor/jquery.js"></script>
<script src="/app/module/palette/js/foundation.min.js"></script>
<script>
  var $rows = $(".dashboard .row");
  $(document).foundation();
</script>
