# -*- coding: utf-8 -*-
<%inherit file="layout.mako" />

<%block name="title">
<title>Palette - Manage</title>
</%block>

<section class="secondary-side-bar">
  <h1>Actions</h1>
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
      <a name="popupRestart" class="popup-link inactive" id="restart">
        <i class="fa fa-fw fa-power-off"></i>
        <span>Restart Application</span>
      </a>
    </li>
    <li>
      <a name="popupBackup" class="popup-link inactive" id="backup"> 
        <i class="fa fa-fw fa-upload"></i>
        <span>Backup</span>
      </a>
    </li>
    <li>
      <a name="popupRepairLicense" class="popup-link inactive" id="repair-license">
        <i class="fa fa-fw fa-gavel"></i>
        <span>Repair License</span>
      </a>
    </li>
    <li>
      <a name="popupZiplogs" class="popup-link inactive" id="ziplogs">
        <i class="fa fa-fw fa-archive"></i>
        <span>Make Ziplogs</span>
      </a>
    </li>

  </ul>

  <h5 class="backup-page">Next Scheduled Backup</h5>
  <h5 id="next-backup" class="sub"></h5>

  <div id="backup-list"></div>
</section>

<div class="dynamic-content with-secondary-sidebar">
  <%include file="events.mako" />
</div>

<article class="popup" id="popupStart">
  <section class="popup-body">
    <section class="row">
      <section class="col-xs-12">
        <p>Are you sure you want to start the <br/>Tableau Server?</p>
      </section>
    </section>
    <section class="row">
      <section class="col-xs-6">
        <button id="start-ok" class="p-btn">OK</button>
      </section>
      <section class="col-xs-6">
        <button class="p-btn popup-close">Cancel</button>
      </section>
    </section>
  </section>
  <div class="shade">&nbsp;</div>
</article>

<article class="popup" id="popupStop">
  <section class="popup-body">
    <section class="row">
      <section class="col-xs-12">
        <p>Are you sure you want to stop the <br/>Tableau Server?</p>
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
        <button id="stop-ok" class="p-btn">OK</button>
      </section>
      <section class="col-xs-6">
        <button class="p-btn popup-close">Cancel</button>
      </section>
    </section>
  </section>
  <div class="shade">&nbsp;</div>
</article>

<article class="popup" id="popupBackup">
  <section class="popup-body">
    <section class="row">
      <section class="col-xs-12">
        <p>Are you sure you want to backup?</p>
      </section>
    </section>
    <section class="row">
      <section class="col-xs-6">
        <button id="backup-ok" class="p-btn">OK</button>
      </section>
      <section class="col-xs-6">
        <button class="p-btn popup-close">Cancel</button>
      </section>
    </section>
  </section>
  <div class="shade">&nbsp;</div>
</article>

<article class="popup" id="popupRestart">
  <section class="popup-body">
    <section class="row">
      <section class="col-xs-12">
        <p>Are you sure you want to restart the <br/>Tableau Server?</p>
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
        </ul>
      </section>
    </section>

    <section class="row">
      <section class="col-xs-6">
        <button id="restart-ok" class="p-btn">OK</button>
      </section>
      <section class="col-xs-6">
        <button class="p-btn popup-close">Cancel</button>
      </section>
    </section>
  </section>
  <div class="shade">&nbsp;</div>
</article>

<article class="popup" id="popupRepairLicense">
  <section class="popup-body">
    <section class="row">
      <section class="col-xs-12">
        <p>Are you sure want to repair the license?</p>
      </section>
    </section>
    <section class="row">
      <section class="col-xs-6">
        <button id="repair-license-ok" class="p-btn">OK</button>
      </section>
      <section class="col-xs-6">
        <button class="p-btn popup-close">Cancel</button>
      </section>
    </section>
  </section>
  <div class="shade">&nbsp;</div>
</article>

<article class="popup" id="popupZiplogs">
  <section class="popup-body">
    <section class="row">
      <section class="col-xs-12">
        <p>Are you sure want to run ziplogs?</p>
      </section>
    </section>
    <section class="row">
      <section class="col-xs-6">
        <button id="ziplogs-ok" class="p-btn">OK</button>
      </section>
      <section class="col-xs-6">
        <button class="p-btn popup-close">Cancel</button>
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
            <input type="radio" name="restoreOptions" id="config-and-data" value="config-and-data" checked />
            <label for="config-and-data">Restore data and configuration</label>
          </p>
        </div>
        <div class="radio">
          <p class="radio-text">
            <input type="radio" name="restoreOptions" id="data-only" value="data-only">
              <label for="data-only">Restore data only</label>
          </p>
        </div>
      </section>
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
        </ul>
      </section>
      <section class="col-xs-12 run-as-user">
        <p>Tableau 'Run-As-User' Password<br/>(If Any)</p>
        <input type="password" name="password" id="password" />
      </section>
    </section>
    <section class="row">
      <section class="col-xs-6">
        <button id="restore-ok" class="p-btn">OK</button>
      </section>
      <section class="col-xs-6">
        <button class="p-btn popup-close">Cancel</button>
      </section>
    </section>
  </section>
  <div class="shade">&nbsp;</div>
  <input type="hidden" id="restore-filename" />
</article>

<script id="backup-list-template" type="x-tmpl-mustache">
  {{#backups}}
  <h5 class="backup-page">{{type}}</h5>
  <ul>
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
