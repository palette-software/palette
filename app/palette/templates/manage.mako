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
        <button id="start-ok" class="p-btn">OK</button>
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
            <input name="license" type="checkbox" checked/>
            <label class="checkbox">
              Also perform license check
            </label>
          </li>
          <li>
            <input name="backup" type="checkbox" checked/>
            <label class="checkbox">
              Also perform safety backup
            </label>
          </li>
          <li>
            <input name="maint" type="checkbox" checked/>
            <label class="checkbox">
              Also start maintenance webserver
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
        <button id="stop-ok" class="p-btn">OK</button>
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
        <button id="backup-ok" class="p-btn">OK</button>
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
      <section class="col-xs-12">
      <div class="radio">
        <p class="radio-text">
          <input type="radio" name="restore_options" id="data_only" value="data_only" checked>
          <label for=data_only">Restore Data Only</label>
        </p>
      </div>
      <div class="radio">
        <p class="radio-text">
          <input type="radio" name="restore_options" id="config_and_data" value="config_and_data">
          <label for=config_and_data">Restore Configuration and Data</label>
        </p>
      </div>
      </section>
    </section>
    <section class="row">
      <section class="col-xs-6">
        <button class="p-btn popup-close">Cancel</button>
      </section>
      <section class="col-xs-6">
        <button id="restore-ok" class="p-btn">OK</button>
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
    <li><a data-value="{{item}}" href="/rest/backup/location">{{item}}</a></li>
    {{/options}}
  </ul>
</script>

<script src="/app/module/palette/js/vendor/require.js" data-main="/app/module/palette/js/manage.js">
</script>
