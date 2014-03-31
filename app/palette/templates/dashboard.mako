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
</%block>

<div class="row dashboard">
  <div class="large-12 columns">
    <div class="row">
      <div class="large-6 medium-6 small-12 xsmall-12 columns">
        <section class="tile-module">
          <div class="panel-body">
            <div class="title"><span>System Monitor</span></div>
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
            <div class="title"><span>Backup</span></div>
            <section class="backup-status">
              <div>
                <h3>Last: </h3>
                <p id="last">— — — —</p>
              </div>
              <div>
                <h3>Next: </h3>
                <p id="next">${obj.next}</p>
              </div>
            </section>
            <br>
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
            <div class="title"><span>Tableau Support Case Builder</span></div>
            <a href="#" class="tile-button"><span class="fi-check"></span><p>Submit</p></a>
            <p class="tile-advanced">
              <a href="#"><span class="fi-list"></span></a>
            </p>
          </div>
        </section>
      </div>

      <div class="large-6 medium-6 small-12 xsmall-12 columns">
        <section class="tile-module vertical-center">
          <div class="panel-body">
            <div class="title"><span>Manage Tableau Server</span></div>
            <ul class=" small-block-grid-2">
              <li><a id="startButton" href="#" class="tile-button"><span class="fi-play"></span><p>Start</p></a></li>
              <li><a id="stopButton" href="#" class="tile-button"><span class="fi-stop"></span><p>Stop</p></a></li>
            </ul>
            <p id="diskspace" class="large"></p>
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
<script type="text/javascript">
    var viewport = $(window).width();

    if (viewport >= 1200) {
        $('#mainNav ul#nav li.more').bind('mouseenter', function() {
        $(this).find('ul').addClass('visible');
        });
        $('#mainNav ul#nav li.more').bind('mouseleave', function() {
            $(this).find('ul').removeClass('visible');
        });     
    } 
    else {
        

        $('li.more > a').bind('click', function() {
            event.preventDefault();
        });

        $('#mainNav ul#nav > li.more').bind('click', function() {
          $(this).find('ul').toggleClass('visible');
        });

        $('#toggle-main-menu').bind('click', function() {
            $('#mainNav ul#nav').toggleClass('visible');
            $(this).toggleClass('visible');
        });
    }
    
</script>