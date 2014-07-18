# -*- coding: utf-8 -*-
<%inherit file="layout.mako" />

<%block name="title">
<title>Palette - User Configuration</title>
</%block>

<style>
.small-entry {
  width:55px;
}
</style>

<section class="dynamic-content">
  <h1 class="page-title">Storage</h1>

  <!--
  <h2>Please choose a storage location</h2>
  <section class="row">
    <section class="col-xs-12 event-dropdowns">
      <div id="event-dropdown" class="btn-group"></div>
    </section>
  </section>
  -->

  <h3>Alert When My Server Attached and Palette Cloud Storage Volumes Attain These Thresholds</h3>

  <p>Warning Alert at <input type="number" class="small-entry"> Error Alert at <input type="number" class="small-entry"/> %</p>
  
  <h3>Encrypt Palette Generated Files (COMING SOON)</h3>
  <p>Encrypts your Palette generated Tableau backups, logs and workbooks using industry standard AES256 2048bit encryption adding another level of security.</p>
  <input type="checkbox" class="ios-checkbox">

  <h2>Backups</h2>
  <h3>Daily Scheduled Backups to Retain</h3>
  <p>The number of daily backups you want Palette to keep in storage</p>
  <input type="number" class="small-entry"> Backups

  <h3>User Generated Backups to Retain</h3>
  <p>The number of user generated Tableau .tsbak backups you want Palette to keep in storage</p>
  <input type="number" class="small-entry"> Backups  

  <h2>Logfiles</h2>
  <h3>Log File Archives to Retain</h3>
  <p>The number of Tableau logfile archives you want Palette to keep in storage</p>
  <input type="number" class="small-entry"> Log Archives

  <h2>Workbooks</h2>
  <h3>Archive Workbooks Only as .twb Files (COMING SOON)</h3>
  <p>Workbook .twb files are just small configuration files, while .twbx are configuration plus extract data which can become very large files</p>
  <input type="checkbox" class="ios-checkbox">
</section>

<script id="event-dropdown-template" type="x-tmpl-mustache">
  <button type="button" class="btn btn-default dropdown-toggle" data-toggle="dropdown"><div data-id="{{id}}">{{value}}</div><span class="caret"></span>
  </button>
  <ul class="dropdown-menu" role="menu">
    {{#options}}
    <li><a data-id="{{id}}">{{item}}</a></li>
    {{/options}}
  </ul>
</script>

<script src="/app/module/palette/js/vendor/require.js" data-main="/app/module/palette/js/users.js">
</script>
