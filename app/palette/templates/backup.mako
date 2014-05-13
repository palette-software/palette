# -*- coding: utf-8 -*-
<%inherit file="layout.mako" />

<%block name="title">
<title>Palette - Backup/Restore</title>
</%block>

<section class="secondary-side-bar">
  <a class="Psmall-only" id="toggle-events" href="#"><i class="fa"></i></a>
  <h2>Actions</h2>
  <ul class="actions">
    <li>
      <a href="#" id="backup" class="inactive"> 
        <i class="fa fa-fw fa-upload"></i>
        <span>Backup</span>
      </a>
    </li>
    <li>
      <a href="#" id="restore" class="inactive"> 
        <i class="fa fa-fw fa-download"></i>
        <span>Restore</span>
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

<script id="backup-list-template" type="x-tmpl-mustache">
  {{#backups}}
  <h5 class="backup-page">{{type}}</h5>
  <ul class="Logs">
    {{#items}}
    <li class="backup">{{creation-time}}</li>
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

<script src="/app/module/palette/js/vendor/require.js" data-main="/app/module/palette/js/backup.js"></script>
