# -*- coding: utf-8 -*-
<%inherit file="webapp.mako" />

<%block name="title">
<title>Palette - Alerting configuration</title>
</%block>

<div class="content general-page">
  <div>
    <div class="top-zone">
      <h1>Alerting Configuration</h1>
    </div> <!-- top-zone -->

    <div class="bottom-zone">
      <a name="monitoring"></a>
      <hr />
      <section class="form-group" id="monitoring">
        <a id="229216" data-toggle="help" href="#"><i class="help"></i></a>

        <div>
          <h3>Storage</h3>
          <p>Alert when my Machine attached volumes exceed these thresholds.</p>
          <p>
            <span>Warning Alert at <span id="disk-watermark-low" class="btn-group percentage"></span></span>&nbsp;<span>Error Alert at <span id="disk-watermark-high" class="btn-group percentage"></span></span>
          </p>
        </div>
        <div>
          <h3>CPU</h3>
          <p>Alert when the average CPU of my Machine(s) exceeds these thresholds for this duration.</p>
          <p>
            <span>Warning Alert at <span id="cpu-load-warn" class="btn-group percentage"></span></span>&nbsp;<span>for <span id="cpu-period-warn" class="btn-group time"></span></span>
          </p>
          <p>
            <span>Error Alert at <span id="cpu-load-error" class="btn-group percentage"></span></span>&nbsp;<span>for <span id="cpu-period-error" class="btn-group time"></span></span>
          </p>
        </div>
        <div>
          <h3>Workbook</h3>
          <p>Alert when workbook web view Page Load Times exceed these thresholds.</p>
          <p>
            Warning Alert at <span id="http-load-warn" class="btn-group percentage up"></span>&nbsp;Error Alert at <span id="http-load-error" class="btn-group percentage up"></span>
          </p>
        </div>
        <div class="save-cancel">
          <button type="button" id="cancel-monitors" class="cancel disabled">
            Cancel
          </button>
          <button type="button" id="save-monitors" class="save disabled">
            Save
          </button>
        </div>
      </section> <!-- section monitoring -->
    </div> <!-- bottom-zone -->
  </div>
</div> <!-- content -->

<script src="/js/vendor/require.js" data-main="/js/alerts.js">
</script>
