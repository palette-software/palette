# -*- coding: utf-8 -*-
<%inherit file="layout.mako" />

<%block name="title">
<title>Palette - User Configuration</title>
</%block>

<style>
h2 {
  text-transform: uppercase;
}
</style>

<section class="dynamic-content storage-page">
  <section class="top-zone">
    <section class="row">
      <section class="col-xs-12">
        <h1 class="page-title">Storage</h1>
      </section>
    </section>
    <section class="row">
      <section class="col-xs-12">
         <p>Settings for your Palette generated Tableau backups, logfiles, workbooks and other files</p>

         <h2>Storage Location</h2>

         <div class="btn-group" id="storage-destination"
              data-href="/rest/storage/dest">
         </div>
      </section>
    </section>
  </section>

  <section>
    <h3>Alert When My Server Attached and Palette Cloud Storage Volumes Attain These Thresholds</h3>
    <p>Warning Alert at <span id="disk-watermark-low" data-href="/rest/storage/low" class="btn-group"></span> %
      &nbsp; &nbsp; &nbsp; &nbsp;
    Error Alert at <span id="disk-watermark-high" data-href="/rest/storage/high" class="btn-group"></span> %</p>
      
    <h3>Encrypt Palette Generated Files (COMING SOON)</h3>
    <p>Encrypts your Palette generated Tableau backups, logs and workbooks using industry standard encryption adding another level of security.</p>

    <div id="storage-encrypt" class="onoffswitch yesno" data-href="/rest/storage/encryption"></div>

    <h2>Backups</h2>
    <h3>Daily Scheduled Backups to Retain</h3>
    <p>The number of daily backups you want Palette to keep in storage</p>
    <p><span id="backup-auto-retain-count" data-href="/rest/storage/auto" class="btn-group"></span> Backups</p>

    <h3>User Generated Backups to Retain</h3>
    <p>The number of user generated Tableau .tsbak backups you want Palette to keep in storage</p>
    <p><span id="backup-user-retain-count" data-href="/rest/storage/user" class="btn-group"></span> Backups</P>

    <h2>Logfiles</h2>
    <h3>Log File Archives to Retain</h3>
    <p>The number of Tableau logfile archives you want Palette to keep in storage</p>
    <p><span id="log-archive-retain-count" data-href="/rest/storage/logs" class="btn-group"></span> Log Archives</p>

    <h2>Workbooks</h2>
    <h3>Archive Workbooks Only as .twb Files (COMING SOON)</h3>
    <p>Workbook .twb files are just small configuration files, while .twbx are configuration plus extract data which can become very large files</p>
    <div id="workbook-as-twb" class="onoffswitch yesno" data-href="/rest/storage/twb"></div>

    </section>
  </section>
</section>

<script id="dropdown-template" type="x-tmpl-mustache">
  <button type="button" class="btn btn-default dropdown-toggle" data-toggle="dropdown"><div data-id="{{id}}">{{value}}</div><span class="caret"></span>
  </button>
  <ul class="dropdown-menu" role="menu">
    {{#options}}
    <li><a data-id="{{id}}">{{item}}</a></li>
    {{/options}}
  </ul>
</script>

<script src="/app/module/palette/js/vendor/require.js" data-main="/app/module/palette/js/storage.js">
</script>
