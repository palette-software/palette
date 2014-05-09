# -*- coding: utf-8 -*-
<%inherit file="layout.mako" />

<%block name="title">
<title>Palette - Backup/Restore</title>
</%block>

<section class="secondary-side-bar">
  <a class="Psmall-only" id="toggle-events" href="#"><i class="fa"></i></a>
  <ul class="actions">
    <li>
      <a href="#" id="backup" class="inactive"> 
        <i class="fa fa-fw fa-download"></i>
        <span>Backup</span>
      </a>
    </li>
    <li>
      <a href="#" id="restore" class="inactive"> 
        <i class="fa fa-fw fa-repeat"></i>
        <span>Restore</span>
      </a>
    </li>
  </ul>
  <h5 class="sub">Archive Backups to</h5>
  <div id="archive-backup" class="btn-group dropdown"></div>
  <div id="backup-list"></div>
</section>

<%include file="events.mako" />

<script id="backup-list-template" type="x-tmpl-mustache">
  {{#backups}}
  <h5>{{type}}</h5>
  <ul class="Logs">
    {{#items}}
    <li><a href="#">{{creation-time}}</a></li>
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
