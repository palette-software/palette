# -*- coding: utf-8 -*-
<%inherit file="layout.mako" />

<%block name="title">
<title>Palette - General Configuration</title>
</%block>

<section class="dynamic-content storage-page">
  <section class="top-zone">
    <section class="row">
      <section class="col-xs-12">
        <h1 class="page-title">General Configuration</h1>
      </section>
    </section>
    <section class="row">
      <section class="col-xs-12">
         <p>Settings for your Palette generated Tableau backups, logfiles, workbooks and other files</p>

         <h2 class="page-subtitle">Storage Location</h2>

         <div class="btn-group" id="storage-destination"
              data-href="/rest/general/dest">
         </div>
      </section>
    </section>
  </section>

  <section>
    <h3>Alert When My Server Attached and Palette Cloud Storage Volumes Attain These Thresholds</h3>
    <p>
      <span>Warning Alert at <span id="disk-watermark-low" data-href="/rest/general/low" class="btn-group"></span> %</span>
      &nbsp;<span>Error Alert at <span id="disk-watermark-high" data-href="/rest/general/high" class="btn-group"></span> %</span>
    </p>

    <h3>Encrypt Palette Generated Files (COMING SOON)</h3>
    <p>Encrypts your Palette generated Tableau backups, logs and workbooks using industry standard encryption adding another level of security.</p>

    <div id="storage-encrypt" class="onoffswitch yesno" data-href="/rest/general/encryption"></div>

    <h2 class="page-subtitle">Backups</h2>
    <h3>Daily Scheduled Backups to Retain</h3>
    <p>The number of daily backups you want Palette to keep in storage</p>
    <p><span id="backup-auto-retain-count" data-href="/rest/general/auto" class="btn-group"></span> Backups</p>

    <h3>User Generated Backups to Retain</h3>
    <p>The number of user generated Tableau .tsbak backups you want Palette to keep in storage</p>
    <p><span id="backup-user-retain-count" data-href="/rest/general/user" class="btn-group"></span> Backups</P>

    <h2 class="page-subtitle">Logfiles</h2>
    <h3>Log File Archives to Retain</h3>
    <p>The number of Tableau logfile archives you want Palette to keep in storage</p>
    <p><span id="log-archive-retain-count" data-href="/rest/general/logs" class="btn-group"></span> Log Archives</p>

    <h2 class="page-subtitle">Workbooks</h2>
    <h3>Archive Workbooks Only as .twb Files (COMING SOON)</h3>
    <p>Workbook .twb files are just small configuration files, while .twbx are configuration plus extract data which can become very large files</p>
    <div id="workbook-as-twb" class="onoffswitch yesno" data-href="/rest/general/twb"></div>

    <h2 class="page-subtitle">Tableau Web Requests</h2>
    <h3>Alert When Tableau Web Requests take longer than These Thresholds</h3>
    <p>
      Warning Alert at <span id="http-load-warn" data-href="/rest/general/http_load_warn" class="btn-group up"></span>
      &nbsp;Error Alert at <span id="http-load-error" data-href="/rest/general/http_load_error" class="btn-group up"></span>
    </p>

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

<script src="/app/module/palette/js/vendor/require.js" data-main="/app/module/palette/js/general.js">
</script>
