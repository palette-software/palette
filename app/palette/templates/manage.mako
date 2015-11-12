# -*- coding: utf-8 -*-
<%inherit file="webapp.mako" />

<%block name="title">
<title>Palette - Manage</title>
</%block>

<section class="secondary-side-bar actions-side-bar">
  <h1>Actions</h1>
  <ul class="actions">
    <li>
      <a id="start" class="inactive"
         data-toggle="modal-popup"
         data-text="Are you sure you want to start the Tableau Server?"> 
        <i class="fa fa-fw fa-play"></i>
        <span>Start Application</span>
      </a>
    </li>
    <li>
      <a id="stop" class="inactive"
         data-toggle="modal-popup" data-target="popupStop">
        <i class="fa fa-fw fa-stop"></i>
        <span>Stop Application</span>
      </a>
    </li>
    <li>
      <a id="restart" class="inactive"
         data-toggle="modal-popup" data-target="popupRestart">
        <i class="fa fa-fw fa-power-off"></i>
        <span>Restart Application</span>
      </a>
    </li>
    <li>
      <a id="backup" class="inactive"
         data-toggle="modal-popup"
         data-text="Are you sure you want to backup?">
        <i class="fa fa-fw fa-upload"></i>
        <span>Backup</span>
      </a>
    </li>
    <li>
      <a id="repair-license" class="inactive"
         data-toggle="modal-popup"
         data-text="Are you sure want to repair the license?">
        <i class="fa fa-fw fa-gavel"></i>
        <span>Repair License</span>
      </a>
    </li>
    <li>
      <a id="ziplogs" class="inactive"
         data-toggle="modal-popup"
	     data-text="Are you sure want to run ziplogs?">
        <i class="fa fa-fw fa-archive"></i>
        <span>Make Ziplogs</span>
      </a>
    </li>

  </ul>

  <h5 class="backup-page">Next Scheduled Backup</h5>
  <h5 id="next-backup" class="sub"></h5>

  <div id="backup-list"></div>
</section>

<%include file="events.mako" />

<script id="backup-list-template" type="x-tmpl-mustache">
  {{#backups}}
  <h5 class="backup-page">{{type}}</h5>
  <ul>
    {{#items}}
    <li class="backup">
      <a class="inactive"
         data-toggle="modal-popup"
         data-target="restore-dialog">
        <span class="timestamp">{{creation-time}}</span>
        <span class="filename">{{name}}</span>
      </a>
    </li>
    {{/items}}
  </ul>
  {{/backups}}
</script>

<script src="/js/vendor/require.js" data-main="/js/manage.js">
</script>

<%block name="popups">
<article class="popup" id="popupStop">
  <section class="popup-body">
    <div>
      <div>
        <p>Are you sure you want to stop the <br/>Tableau Server?</p>
      </div>
      <div>
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
      </div>
      <div>
        <button class="cancel">Cancel</button>
        <button id="stop-ok" class="ok">OK</button>
      </div>
    </div>
  </section>
  <div class="shade">&nbsp;</div>
</article>

<article class="popup" id="popupRestart">
  <section class="popup-body">
    <div>
      <div>
        <p>Are you sure you want to restart the Tableau Server?</p>
      </div>
      <div>
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
      </div>
      <div>
        <button class="cancel">Cancel</button>
        <button id="restart-ok" class="ok">OK</button>
      </div>
    </div>
  </section>
  <div class="shade">&nbsp;</div>
</article>

<article class="popup popup-tall" id="restore-dialog">
  <section class="popup-body">
    <div>
      <div>
        <p>Are you sure want to restore from<br/><span id="restore-timestamp"></span>?</p>
      </div>
      <div>
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
      </div>
      <div>
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
      </div>
      <div class=" run-as-user">
        <p>Tableau 'Run-As-User' Password<mbr/>(If Any)</p>
        <input type="password" name="password" id="password" />
      </div>
      <div class="save-cancel">
        <button class="cancel">Cancel</button>
        <button id="restore-ok" class="ok">OK</button>
      </div>
    </div>
  </section>
  <div class="shade">&nbsp;</div>
  <input type="hidden" id="restore-filename" />
</article>
</%block> <!-- popups -->
