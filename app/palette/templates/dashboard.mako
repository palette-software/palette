# -*- coding: utf-8 -*- 
<%inherit file="layout.mako" />

<%block name="style">
<link href="http://fonts.googleapis.com/css?family=Roboto:300,400,700|Lato:100,300,400" rel="stylesheet" type="text/css">
<link rel="stylesheet" type="text/css" href="/app/module/palette/css/style.css" media="screen">
</%block>

<h1>Palette Software</h1>
<div class="tile">
  <h2>System Monitor</h2>
  <div id="green" class="green-light" style="display:none"></div>
  <div id="orange" class="orange-light" style="display:none"></div>
  <div id="red" class="red-light" style="display:none"></div>
  <p id="status-message" class="large"></p>
  <p class="tile-advanced">
    <span class="arrow-down"></span>
    <a id="advanced-status" href="#"> Advanced</a>
  </p>
</div>
<div class="tile">
  <h2>Backup</h2>
  <h3>Last</h3>
  <p id="last">Thursday, November 7th at 12:00 AM</p>
  <h3>Next</h3>
  <p id="next">Friday, November 8th at 12:00 AM</p>
  <p class="padtop">
    <a id="backupButton" class="button spacer">Backup</a>
    <a id="restoreButton" class="button">Restore</a></p>
  <p class="tile-advanced"><span class="arrow-down"></span> Advanced</p>
</div>
<div class="tile">
  <h2>Tableau Support Case Builder</h2>
  <p class="doublepadtop"><a class="button spacer">Standard</a> <a class="button">Priority</a></p>
  <p class="tile-advanced"><span class="arrow-down"></span> Advanced</p>
</div>
<div class="tile">
  <h2>Manage Tableau Server</h2>
  <p class="pad doublepadtop"><a class="button spacer">Start</a> <a class="button">Stop</a></p>
  <p class="padtop large">105 Days of Disk Space</p>
  <p class="tile-advanced"><span class="arrow-down"></span> Advanced</p>
</div>

<script>
require({
  packages: [
    { name: "palette", location: "/app/module/palette/js" }
  ]
}, [ "palette/monitor", "palette/backup" ]);
</script>

