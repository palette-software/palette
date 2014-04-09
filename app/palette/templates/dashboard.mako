# -*- coding: utf-8 -*- 
<%inherit file="_layout.mako" />

<%block name="title">
<title>Palette</title>
</%block>

<%block name="favicon">
<%include file="favicon.mako" />
</%block>
<%block name="fullstyle">
<meta charset="utf-8">
<meta name="viewport" content="initial-scale=1, maximum-scale=1, user-scalable=no, width=device-width">
<link href='http://fonts.googleapis.com/css?family=Roboto:300,500' rel='stylesheet' type='text/css'>
<link rel="stylesheet" type="text/css" href="/app/module/palette/css/foundation.css">
<link rel="stylesheet" type="text/css" href="/app/module/palette/css/foundation-icons.css">
<link rel="stylesheet" type="text/css" href="/app/module/palette/css/normalize.css" media="screen">
<link rel="stylesheet" type="text/css" href="/app/module/palette/css/style.css" media="screen">

<script src="/app/module/palette/js/vendor/modernizr.js"></script>

<style type="text/css">
  #mainNav ul.nav li.active-home a {
    color: #fff;
  }
  @media screen and (max-width: 960px) {
    #mainNav ul.nav li.active-home a {
    color: #8D96A3;
    padding-left:35px;
    }
  }
</style>

</%block>

<section class="row dashboard">
  <section class="large-12 columns">
    <section class="row">
      <section class="large-6 medium-6 small-12 xsmall-12 columns">
        <section class="tile-module">
          <section class="panel-body">
            <section class="title"><span>Status</span></section>
            <section id="green" class="green-light" style="display:none"></section>
            <section id="yellow" class="yellow-light" style="display:none"></section>
            <section id="orange" class="orange-light" style="display:none"></section>
            <section id="red" class="red-light" style="display:none"></section>
            <p id="status-message" class="large"></p>
            <p class="tile-advanced">
              <a id="advanced-status" href="#"><span class="fi-list"></span></a>
            </p>
          </section>
        </section>
      </section>

      <section class="large-6 medium-6 small-12 xsmall-12 columns">
        <section class="tile-module">
          <section class="panel-body">
            <section class="title"><span>Backup</span></section>
            <section class="backup-status">
              <section>
                <h3>Last: </h3>
                <p id="last">— — — —</p>
              </section>
              <section>
                <h3>Next: </h3>
                <p id="next">${obj.next}</p>
              </section>
            </section>
            <br>
            <ul class="small-block-grid-2">
              <li><a id="backupButton" class="tile-button"><span class="fi-download"></span><p>Backup</p></a></li>
              <li><a id="restoreButton" class="tile-button"><span class="fi-arrow-left"></span><p>Restore</p></a></li>
            </ul>
            <p class="tile-advanced">
              <a id="advanced-backup" href="#"><span class="fi-list"></span></a>
            </p>
          </section>
        </section>
      </section>
    </section>
    <section class="row">
      <section class="large-6 medium-6 small-12 xsmall-12 columns">
        <section class="tile-module">
          <section class="panel-body">
            <section class="title"><span>Tableau Support Case Builder</span></section>
            <a href="#" class="tile-button"><span class="fi-check"></span><p>Submit</p></a>
            <p class="tile-advanced">
              <a href="#"><span class="fi-list"></span></a>
            </p>
          </section>
        </section>
      </section>

      <section class="large-6 medium-6 small-12 xsmall-12 columns">
        <section class="tile-module vertical-center">
          <section class="panel-body">
            <section class="title"><span>Manage Tableau Server</span></section>
            <ul class=" small-block-grid-2">
              <li><a id="startButton" href="#" class="tile-button"><span class="fi-play"></span><p>Start</p></a></li>
              <li><a id="stopButton" href="#" class="tile-button"><span class="fi-stop"></span><p>Stop</p></a></li>
            </ul>
            <p id="diskspace" class="large"></p>
            <p class="tile-advanced">
              <a id="advanced-manage" href="#"><span class="fi-list"></span></a>
            </p>
          </section>
        </section>
      </section>
    </section>
  </section>
</section>
    <!--
    <section class="tile">
      <h2 class="bottomRow">Manage Tableau Server</h2>
      <p class="pad">
        <a id="startButton" href="#" class="button spacer disabled">Start</a>
        <a id="stopButton" href="#" class="button">Stop</a>
      </p>
      <p id="diskspace" class="large"></p>
      <p class="tile-advanced">
        <a id="advanced-manage" href="#"><span class="fi-list"></span></a>
      </p>
    </section>
  </section>
</section>-->

<script>
require({
  packages: [
    { name: "palette", location: "/app/module/palette/js" }
  ]
}, [ "palette/monitor", "palette/backup", "palette/manage" ]);
</script>

<%include file="commonjs.mako" />