# -*- coding: utf-8 -*-
<%inherit file="layout.mako" />

<%block name="title">
<title>Palette - Manage</title>
</%block>

<section class="secondary-side-bar">
  <h2>Actions</h2>
  <ul class="actions">
    <li>
      <a name="popupStart" class="popup-link inactive" id="start"> 
        <i class="fa fa-fw fa-play"></i>
        <span>Start Application</span>
      </a>
    </li>
    <li>
      <a name="popupStop" class="popup-link inactive" id="stop"> 
        <i class="fa fa-fw fa-stop"></i>
        <span>Stop Application</span>
      </a>
    </li>
    <li>
      <a name="popupBackup" class="popup-link inactive" id="backup"> 
        <i class="fa fa-fw fa-upload"></i>
        <span>Backup</span>
      </a>
    </li>
  </ul>

  <h5 class="backup-page">Next Scheduled Backup</h5>
  <h5 id="next-backup" class="sub"></h5>

  <h5 class="backup-page">Backup Archive Location</h5>
  <div id="archive-backup" class="btn-group dropdown"></div>

  <div id="backup-list"></div>
</section>

<section class="dynamic-content with-secondary-sidebar">
  <%include file="events.mako" />
</section>

<article class="popup" id="popupStart">
  <section class="popup-body">
    <section class="row">
      <section class="col-xs-12">
        <p>Are you sure want to start the <br/>Tableau Server?</p>
      </section>
    </section>
    <section class="row">
      <section class="col-xs-6">
        <button class="p-btn popup-close">Cancel</button>
      </section>
      <section class="col-xs-6">
        <button id="start-ok" class="p-btn">Start</button>
      </section>
    </section>
  </section>
  <div class="shade">&nbsp;</div>
</article>

<article class="popup" id="popupStop">
  <section class="popup-body">
    <section class="row">
      <section class="col-xs-12">
        <p>Are you sure want to stop the <br/>Tableau Server?</p>
      </section>
    </section>
    <section class="row">
      <section class="col-xs-12">
        <ul class="checkbox">
          <li>
            <input type="checkbox" checked/>
            <label class="checkbox">
              <span></span>
              Confirm license validity
            </label>
          </li>
          <li>
            <input type="checkbox" checked/>
            <label class="checkbox">
              <span></span>
              Backup rollback protection
            </label>
          </li>
        </ul>
      </section>
    </section>

    <section class="row">
      <section class="col-xs-6">
        <button class="p-btn popup-close">Cancel</button>
      </section>
      <section class="col-xs-6">
        <button id="stop-ok" class="p-btn">Stop</button>
      </section>
    </section>
  </section>
  <div class="shade">&nbsp;</div>
</article>

<article class="popup" id="popupBackup">
  <section class="popup-body">
    <section class="row">
      <section class="col-xs-12">
        <p>Are you sure want to backup?</p>
      </section>
    </section>
    <section class="row">
      <section class="col-xs-6">
        <button class="p-btn popup-close">Cancel</button>
      </section>
      <section class="col-xs-6">
        <button id="backup-ok" class="p-btn">Backup</button>
      </section>
    </section>
  </section>
  <div class="shade">&nbsp;</div>
</article>

<article class="popup" id="restore-dialog">
  <section class="popup-body">
    <section class="row">
      <section class="col-xs-12">
        <p>Are you sure want to restore from<br/><span id="restore-timestamp"></span>?</p>
      </section>
    </section>
    <section class="row">
      <section class="col-xs-6">
        <button class="p-btn popup-close">Cancel</button>
      </section>
      <section class="col-xs-6">
        <button id="restore-ok" class="p-btn">Restore</button>
      </section>
    </section>
  </section>
  <div class="shade">&nbsp;</div>
  <input type="hidden" id="restore-filename" />
</article>

<script id="backup-list-template" type="x-tmpl-mustache">
  {{#backups}}
  <h5 class="backup-page">{{type}}</h5>
  <ul class="Logs">
    {{#items}}
    <li class="backup">
      <a class="inactive">
        <span class="timestamp">{{creation-time}}</span>
        <span class="filename">{{name}}</span>
      </a>
    </li>
    {{/items}}
  </ul>
  {{/backups}}
</script>

<script id="archive-backup-template" type="x-tmpl-mustache">
  <button type="button" class="btn btn-default dropdown-toggle"
          data-toggle="dropdown"><div>{{value}}</div><span class="caret"></span>
  </button>
  <ul class="dropdown-menu" role="menu">
    {{#options}}
    <li><a href="#">{{item}}</a></li>
    {{/options}}
  </ul>
</script>

<script src="/app/module/palette/js/vendor/require.js" data-main="/app/module/palette/js/manage.js">
</script>
