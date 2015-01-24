# -*- coding: utf-8 -*-
<%inherit file="../layout.mako" />

<%block name="title">
<title>Palette - General Configuration</title>
</%block>

<div class="dynamic-content configuration general-page">
  <div class="scrollable">

    <a name="storage"></a>
    <section class="top-zone">
      <section class="row">
        <section class="col-xs-12">
          <h1 class="page-title">General Configuration</h1>
        </section>
      </section>
    </section>

    <section id="storage">
      <h2>Storage Location</h2>
      <input type="radio" id="storage-local" name="storage-type" value="local" />
      <label for="storage-local">My Machine</label>
      <input type="radio" id="storage-s3" name="storage-type" value="s3" />
      <label for="storage-s3">Amazon S3</label>
      <input type="radio" id="storage-gcs" name="storage-type" value="gcs" />
      <label for="storage-gcs">Google Cloud Storage</label>
      <section id="local" class="hidden">
	<span class="btn-group" id="storage-destination"></span>
	<div>
          <button type="button" id="save-local" class="btn btn-primary">
            Save
          </button>
          <button type="button" id="cancel-local" class="btn btn-primary">
            Cancel
          </button>
        </div>
      </section>
      <section id="s3" class="hidden">
        <h3>Credentials</h3>
        <label for="s3-access-key">Access Key ID</label>
        <input type="text" id="s3-access-key" />
        <label for="s3-secret-key">Secret Access Key</label>
        <input type="password" id="s3-secret-key" />
        <label for="s3-url">S3 URL or Bucket Name</label>
        <input type="text" id="s3-url" />
        <div class="btn-bar">
          <button type="button" id="test-s3" class="btn btn-test okcancel"
                  data-text="Are you sure you want to delete the S3 credentials?">
            Test Connection
          </button>

          <button type="button" id="remove-s3" class="btn btn-test okcancel"
                  data-text="Are you sure you want to delete the S3 credentials?">
            Remove Credentials
          </button>
        </div>
        <div>
          <button type="button" id="save-s3" class="btn btn-primary">
            Save
          </button>
          <button type="button" id="cancel-s3" class="btn btn-primary">
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
          <button type="button" id="test-gcs" class="btn btn-test okcancel"
                  data-text="Are you sure you want to delete the GCS credentials?">
            Test Connection
          </button>

          <button type="button" id="remove-gcs" class="btn btn-test okcancel"
                  data-text="Are you sure you want to delete the GCS credentials?">
            Remove Credentials
          </button>
        </div>
        <div>
          <button type="button" id="save-gcs" class="btn btn-primary">
            Save
          </button>
          <button type="button" id="cancel-gcs" class="btn btn-primary">
            Cancel
          </button>
        </div>
      </section>
    </section>

    <a name="email-alerts"></a>
    <hr />
    <section id="email-alerts">
      <h2>Email Alerts</h2>
      <p class="slider-group">
        <span>Send Alerts to Palette Admins
          <span id="alert-admins" class="onoffswitch yesno"></span>
        </span>&nbsp;
        <span>
          Send Alerts to Palette Publishers
          <span id="alert-publishers" class="onoffswitch yesno"></span>
        </span>
      </p>
      <div>
        <button type="button" id="save-email-alerts" class="btn btn-primary disabled">
          Save
        </button>
        <button type="button" id="cancel-email-alerts" class="btn btn-primary disabled">
          Cancel
        </button>
      </div>
    </section>

    <a name="backups"></a>
    <hr />
    <section id="backups">
      <h2>Backups</h2>
      <p class="slider-group">
        <span>Scheduled Backups
          <span id="scheduled-backups" class="onoffswitch yesno"></span>
        </span>
      </p>
      <h3>Retained Scheduled Backups</h3>
      <p>The number of scheduled Backups you want Palette to keep in storage</p>
      <p><span id="backup-auto-retain-count" class="btn-group count"></span> Backups</p>
<!--
      <h3>Frequency and Time of Scheduled Backups</h3>
      <p>
        <span>Run Backup Every
          <span id="scheduled-backup-period" class="btn-group count"></span> Hours</span>
        &nbsp;<span>Starting at <span id="scheduled-backup-hour" class="btn-group count"></span> : <span id="scheduled-backup-minute" class="btn-group count"></span> : <span id="scheduled-backup-ampm" class="btn-group ampm"></span>
          <span class="timezone"></span></span>
      </p>
-->
      <h3>Retained User Requested Backups</h3>
      <p>The number of user requested Backups you want Palette to keep in storage</p>
      <p>
        <span id="backup-user-retain-count" class="btn-group count"></span> Backups
      </p>
      <div>
        <button type="button" id="save-backups" class="btn btn-primary disabled">
          Save
        </button>
        <button type="button" id="cancel-backups" class="btn btn-primary disabled">
          Cancel
        </button>
      </div>
    </section>

    <a name="ziplogs"></a>
    <hr />
    <section id="ziplogs">
      <h2>Ziplogs</h2>
      <p class="slider-group">
        <span>Scheduled Ziplogs
          <span id="scheduled-ziplogs" class="onoffswitch yesno"></span>
        </span>
      </p>
      <h3>Retained Scheduled Ziplogs</h3>
      <p>The number of scheduled Ziplogs you want Palette to keep in storage</p>
      <p>
        <span id="ziplog-auto-retain-count" class="btn-group count"></span> Ziplogs
      </p>
      <h3>Retained User Requested Ziplogs</h3>
      <p>The number of user requested Ziplogs you want Palette to keep in storage</p>
      <p>
        <span id="ziplog-user-retain-count" class="btn-group count"></span> Ziplogs
      </p>
      <div>
        <button type="button" id="save-ziplogs" class="btn btn-primary disabled">
          Save
        </button>
        <button type="button" id="cancel-ziplogs" class="btn btn-primary disabled">
          Cancel
        </button>
      </div>
    </section>

    <a name="workbooks"></a>
    <hr />
    <section id="workbooks">
      <h2>Workbook Archive</h2>
      <p class="slider-group">
        <span>Archive
          <span id="enable-archive" class="onoffswitch yesno"></span>
        </span>
      </p>
      <div class="row">
        <div class="col-xs-6">
          <h3>Tableau Server Admin Username</h3>
          <input type="text" id="archive-username" />
        </div>
        <div class="col-xs-6">
          <h3>Tableau Server Admin Password</h3>
          <input type="password" id="archive-password" />
        </div>
      </div>
      <div>
        <button type="button" id="save-workbooks" class="btn btn-primary disabled">
          Save
        </button>
        <button type="button" id="cancel-workbooks" class="btn btn-primary disabled">
          Cancel
        </button>
      </div>
    </section>

    <a name="monitoring"></a>
    <hr />
    <section id="monitoring">
      <h2>Monitoring</h2>

      <h3>Storage</h3>
      <p>Alert When My Machine Attached Volumes Exceed These Thresholds</p>
      <p>
        <span>Warning Alert at <span id="disk-watermark-low" data-href="/rest/general/low" class="btn-group"></span> %</span>
        &nbsp;<span>Error Alert at <span id="disk-watermark-high" data-href="/rest/general/high" class="btn-group"></span> %</span>
      </p>

      <section class="cpu">      
        <h3>CPU</h3>
        <p>
          <span>Warning Alert at <span id="cpu-warning" class="btn-group"></span> %</span>
          &nbsp;<span>for <span id="cpu-warning-duration" class="btn-group"></span> minutes</span>
        </p>
        <p>
          <span>Error Alert at <span id="cpu-error" class="btn-group"></span> %</span>
          &nbsp;<span>for <span id="cpu-error-duration" class="btn-group"></span> minutes</span>
        </p>
      </section>
      <hr />

      <section>
        <h2>Workbook</h2>
        <p>Alert When Workbook Web View Load Times Exceed These Thresholds</p>
        <p>
          Warning Alert at <span id="http-load-warn" class="btn-group up"></span>
          &nbsp;Error Alert at <span id="http-load-error" class="btn-group up"></span>
        </p>
      </section>
    </section>
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