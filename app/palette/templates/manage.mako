# -*- coding: utf-8 -*-
<%inherit file="layout.mako" />

<%block name="title">
<title>Palette - Manage</title>
</%block>

<section class="secondary-side-bar">
  <a class="Psmall-only" id="toggle-events" href="#"><i class="fa"></i></a>
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
      <a name="popupRestart" class="popup-link inactive" id="restart"> 
        <i class="fa fa-fw fa-repeat inactive"></i>
        <span>Restart Application</span>
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

<%include file="events.mako" />

<article class="popup" id="popupStart">
  <section class="popup-body">
    <section class="row">
      <section class="col-xs-12">
        <p>Are you sure want to <span class="bold">START</span> the <br/>Tableau Server Application?</p>
      </section>
    </section>
    <section class="row">
      <section class="col-xs-6">
        <button class="p-btn p-btn-grey popup-close">Cancel</button>
      </section>
      <section class="col-xs-6">
        <button id="start-ok" class="p-btn p-btn-grey">Start</button>
      </section>
    </section>
  </section>
  <div class="shade">&nbsp;</div>
</article>

<article class="popup" id="popupStop">
  <section class="popup-body">
    <section class="row">
      <section class="col-xs-12">
        <p>Are you sure want to <span class="bold">STOP</span> the <br/>Tableau Server Application?</p>
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
        <button class="p-btn p-btn-grey popup-close">Cancel</button>
      </section>
      <section class="col-xs-6">
        <button id="stop-ok" class="p-btn p-btn-grey">Stop</button>
      </section>
    </section>
  </section>
  <div class="shade">&nbsp;</div>
</article>

<article class="popup" id="popupRestart">
  <section class="popup-body">
    <section class="row">
      <section class="col-xs-12">
        <p>Are you sure want to <span class="bold">RESTART</span> the <br/>Tableau Server Application?</p>
      </section>
    </section>
    <section class="row">
      <section class="col-xs-6">
        <button class="p-btn p-btn-grey popup-close">Cancel</button>
      </section>
      <section class="col-xs-6">
        <button id="restart-ok" class="p-btn p-btn-grey">Restart</button>
      </section>
    </section>
  </section>
  <div class="shade">&nbsp;</div>
</article>

<article class="popup" id="popupBackup">
  <section class="popup-body">
    <section class="row">
      <section class="col-xs-12">
        <p>Are you sure want to <span class="bold">BACKUP</span> the <br/>Tableau Server Application?</p>
      </section>
    </section>
    <section class="row">
      <section class="col-xs-6">
        <button class="p-btn p-btn-grey popup-close">Cancel</button>
      </section>
      <section class="col-xs-6">
        <button id="backup-ok" class="p-btn p-btn-grey">Backup</button>
      </section>
    </section>
  </section>
  <div class="shade">&nbsp;</div>
</article>

 <article class="popup" id="popupRestore">
  <section class="popup-body">
    <section class="row">
      <section class="col-xs-12">
        <p>Are you sure want to <span class="bold">restore</span> the Tableau Server Application with backup from <span class="bold"> 12:00 AM on April 15, 2014</span>?</p>
      </section>
    </section>
    <section class="row">
      <section class="col-xs-12">
        <ul class="radio">
          <li>
            <input type="radio" name="restorepoint">
              <label class="radio">
                <span></span>
                <div>(4/23/2014) -</div> Backup
              </label>
          </li>
          <li>
            <input type="radio" name="restorepoint">
              <label class="radio">
                <span></span>
                <div>(4/18/2014) -</div> Backup 2
              </label>
          </li>
          <li>
            <input type="radio" name="restorepoint">
              <label class="radio">
                <span></span>
                <div>(4/7/2014) -</div> Backup 3
              </label>
          </li>
        </ul>
        <ul class="checkbox">
          <li>
            <input type="checkbox">
              <label class="checkbox">
                <span></span>
                With configureation settings
              </label>
          </li>
          <li>
            <input type="checkbox">
              <label class="checkbox">
                <span></span>
                With backup rollback protection
              </label>
          </li>
        </ul>
      </section>
    </section>
    <section class="row">
      <section class="col-xs-6">
        <button class="p-btn p-btn-grey popup-close">Cancel</button>
      </section>
      <section class="col-xs-6">
        <button id="save-ok" class="p-btn p-btn-blue">Restore</button>
      </section>
    </section>
  </section>
  <div class="shade">&nbsp;</div>
</article>

 <article class="popup" id="restore-dialog">
  <section class="popup-body">
    <section class="row">
      <section class="col-xs-12">
        <p>Are you sure want to <span class="bold">RESTORE</span> the Tableau Server Application with backup from <span class="bold" id="restore-timestamp"></span>?</p>
      </section>
    </section>
    <section class="row">
      <section class="col-xs-6">
        <button class="p-btn p-btn-grey popup-close">Cancel</button>
      </section>
      <section class="col-xs-6">
        <button id="restore-ok" class="p-btn p-btn-grey">Restore</button>
      </section>
    </section>
  </section>
  <div class="shade">&nbsp;</div>
</article>

<script id="backup-list-template" type="x-tmpl-mustache">
  {{#backups}}
  <h5 class="backup-page">{{type}}</h5>
  <ul class="Logs">
    {{#items}}
    <li class="backup"><a href="#">{{creation-time}}</a></li>
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
