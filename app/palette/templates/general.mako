# -*- coding: utf-8 -*-
<%inherit file="layout.mako" />

<%block name="title">
<title>Palette - General Configuration</title>
</%block>

<div class="dynamic-content configuration general-page">
  <div class="scrollable">
    <section class="top-zone">
      <section class="row">
        <section class="col-xs-12">
          <h1 class="page-title">General Configuration</h1>
        </section>
      </section>
    </section>

    <section>
      <h2>Storage Location</h2>
      <!-- data-href="/rest/general/dest" -->
      <input type="radio" id="storage-none" name="storage-type" value="none" />
      <label for="storage-none">None</label>
      <input type="radio" id="storage-s3" name="storage-type" value="s3" />
      <label for="storage-s3">Amazon S3</label>
      <input type="radio" id="storage-gcs" name="storage-type" value="gcs" />
      <label for="storage-gcs">Google Cloud Storage</label>
      <input type="radio" id="storage-local" name="storage-type" value="local" />
      <label for="storage-local">My Machine</label>
      <section id="s3" class="hidden">
	<h3>Credentials</h3>
        <label for="s3-access-key">Access Key ID</label>
	<input type="text" id="s3-access-key" />
        <label for="s3-secret-key">Secret Access Key</label>
        <input type="password" id="s3-secret-key" />
	<label for="s3-url">S3 URL or Bucket Name</label>
        <input type="text" id="s3-url" />
	<div class="btn-bar">
	  <button type="button" id="delete" class="btn btn-test okcancel"
                  data-text="Are you sure you want to delete the S3 credentials?">
            Test Connection
          </button>

	  <button type="button" id="delete" class="btn btn-test okcancel"
                  data-text="Are you sure you want to delete the S3 credentials?">
            Remove Credentials
          </button>
	</div>
        <div>
          <button type="button" id="save" class="btn btn-primary disabled">
            Save
          </button>
          <button type="button" id="cancel" class="btn btn-primary">
            Cancel
          </button>
        </div>
      </section>
      <section id="gcs" class="hidden">
	<h3>Credentials</h3>
        <label for="gcs-access-key">Access Key ID</label>
	<input type="text" id="gcs-access-key" />
        <label for="gcs-secret-key">Secret Access Key</label>
        <input type="password" id="gcs-secret-key" />
	<label for="gcs-url">GCS URL or Bucket Name</label>
        <input type="text" id="gcs-url" />
	<div class="btn-bar">
	  <button type="button" id="delete" class="btn btn-test okcancel"
                  data-text="Are you sure you want to delete the GCS credentials?">
            Test Connection
          </button>

	  <button type="button" id="delete" class="btn btn-test okcancel"
                  data-text="Are you sure you want to delete the GCS credentials?">
            Remove Credentials
          </button>
	</div>
        <div>
          <button type="button" id="save" class="btn btn-primary disabled">
            Save
          </button>
          <button type="button" id="cancel" class="btn btn-primary">
            Cancel
          </button>
        </div>
      </section>
      <section id="local">
      </section>
    </section>

    <hr />

    <section>
      <h3>Alert When My Server Attached and Palette Cloud Storage Volumes Attain These Thresholds</h3>
      <p>
        <span>Warning Alert at <span id="disk-watermark-low" data-href="/rest/general/low" class="btn-group"></span> %</span>
        &nbsp;<span>Error Alert at <span id="disk-watermark-high" data-href="/rest/general/high" class="btn-group"></span> %</span>
      </p>
    </section>
    <section class="cpu">
      <h2>CPU Monitoring</h2>
      <h3>Alert When Any Monitored Server Attains These Thresholds</h3>
      <p id="cpu-warn">
        <span>Warning Alert at <span id="cpu-load-warn" data-href="/rest/general/cpu/load/warn" class="btn-group"></span> %</span>
        &nbsp;<span>for <span id="cpu-period-warn" data-href="/rest/general/cpu/period/warn" class="btn-group"></span> minutes</span>
      </p>
      <p id="cpu-error">
        <span>Error Alert at <span id="cpu-load-error" data-href="/rest/general/cpu/load/error" class="btn-group"></span> %</span>
        &nbsp;<span>for <span id="cpu-period-error" data-href="/rest/general/cpu/period/error" class="btn-group"></span> minutes</span>
      </p>
    </section>
    <section>
      <h2>Tabcmd User Credentials</h2>
      <p>The Tableau Administrator user credentials used to manage the Palette Workbook Archive</p>
      <h4>Username</h4>
      <p class="editbox"
         data-href="/rest/workbooks/primary/user">
        ${req.primary_user}
      </p>
      <h4>Password</h4>
      <p class="editbox password"
         data-href="/rest/workbooks/primary/password">
        ${req.primary_pw}
      </p>
    </section>
    <section>
      <h2>Backups</h2>
      <h3>Daily Scheduled Backups to Retain</h3>
      <p>The number of daily backups you want Palette to keep in storage</p>
      <p><span id="backup-auto-retain-count" data-href="/rest/general/auto" class="btn-group"></span> Backups</p>
    </section>
    <section>
      <h3>User Generated Backups to Retain</h3>
      <p>The number of user generated Tableau .tsbak backups you want Palette to keep in storage</p>
      <p><span id="backup-user-retain-count" data-href="/rest/general/user" class="btn-group"></span> Backups</P>
    </section>
    <section>
      <h2>Logfiles</h2>
      <h3>Log File Archives to Retain</h3>
      <p>The number of Tableau logfile archives you want Palette to keep in storage</p>
      <p><span id="log-archive-retain-count" data-href="/rest/general/logs" class="btn-group"></span> Log Archives</p>
    </section>
    <section>
      <h2>Tableau Web Requests</h2>
      <h3>Alert When Tableau Web Requests take longer than These Thresholds</h3>
      <p>
        Warning Alert at <span id="http-load-warn" data-href="/rest/general/http_load_warn" class="btn-group up"></span>
        &nbsp;Error Alert at <span id="http-load-error" data-href="/rest/general/http_load_error" class="btn-group up"></span>
      </p>
    </section>
  </div>
</div>

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
