# -*- coding: utf-8 -*- 
<%inherit file="_layout.mako" />

<%block name="title">
<title>Palette</title>
</%block>

<%block name="favicon">
<%include file="favicon.mako" />
</%block>

<%block name="style">
<link href="http://fonts.googleapis.com/css?family=Roboto:300,400,700|Lato:100,300,400" rel="stylesheet" type="text/css">
<link rel="stylesheet" type="text/css" href="/app/module/palette/css/style.css" media="screen">
<link rel="stylesheet" type="text/css" href="/app/module/palette/css/foundation.css">
<link rel="stylesheet" type="text/css" href="/app/module/palette/css/new-style.css">
<script src="/app/module/palette/js/vendor/modernizr.js"></script>
</%block>

<h1>Palette Software</h1>
<div class="row dashboard">
  <div class="large-12 columns">
    <div class="row">
      <div class="large-6 medium-6 xsmall-12 columns">
        <section>
          <div class="panel-title">
            <div class="title">System Monitor</div>
            <div id="green" class="green-light" style="display:none"></div>
            <div id="yellow" class="yellow-light" style="display:none"></div>
            <div id="orange" class="orange-light" style="display:none"></div>
            <div id="red" class="red-light" style="display:none"></div>
            <p id="status-message" class="large"></p>
            <p class="tile-advanced">
              <span class="arrow-down"></span>
              <a id="advanced-status" href="#"> Advanced</a>
            </p>
          </div>
        </section>
      </div>

      <div class="large-6 medium-6 xsmall-12 columns">
        <section>
          <div class="panel-title">
            <div class="title">Backup</div>
            <h3>Last</h3>
            <p id="last">— — — —</p>
            <h3>Next</h3>
            <p id="next">${obj.next}</p>
            <p class="padtop">
              <a id="backupButton" class="button spacer">Backup</a>
              <a id="restoreButton" class="button">Restore</a></p>
            <p class="tile-advanced">
              <span class="arrow-down"></span>
              <a id="advanced-backup" href="#"> Advanced</a>
            </p>
          </div>
        </section>
      </div>
    </div>
    <div class="row">
      <div class="large-6 medium-6 xsmall-12 columns">
        <section>
          <div class="panel-title">
            <div class="title">Tableau Support Case Builder</div>
            <p class="doublepadtop"><a class="button center">Submit</a></p>
            <p class="tile-advanced">
              <span class="arrow-down"></span>
              <a id="advanced-backup" href="#"> Advanced</a>
            </p>
          </div>
        </section>
      </div>

      <div class="large-6 medium-6 xsmall-12 columns">
        <section>
          <div class="panel-title">
            <div class="title">Manage Tableau Server</div>
            <p class="pad doublepadtop">
              <a id="startButton" href="#" class="button spacer disabled">Start</a>
              <a id="stopButton" href="#" class="button">Stop</a>
            </p>
            <p id="diskspace" class="padtop large"></p>
            <p class="tile-advanced">
              <span class="arrow-down"></span>
              <a id="advanced-backup" href="#"> Advanced</a>
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
      <p class="pad doublepadtop">
        <a id="startButton" href="#" class="button spacer disabled">Start</a>
        <a id="stopButton" href="#" class="button">Stop</a>
      </p>
      <p id="diskspace" class="padtop large"></p>
      <p class="tile-advanced">
        <span class="arrow-down"></span>
        <a id="advanced-manage" href="#"> Advanced</a>
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
  $(document).foundation();
</script>
