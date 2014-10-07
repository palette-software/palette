# -*- coding: utf-8 -*-
<%inherit file="layout.mako" />

<%block name="title">
<title>Palette - User Configuration</title>
</%block>

<section class="dynamic-content integration s3">
  <section class="top-zone">
    <section class="row">
      <section class="col-xs-12">
        <h1 class="page-title">Amazon Web Services S3</h1>
      </section>
    </section>
    <section class="row">
      <section class="col-xs-12">
         <p>Cloud storage to save your Tableau backups, logfiles, workbooks and other Palette generated files</p>
         <h2 class="page-subtitle">Credentials</h2>
         <form>
         <h3>Access Key ID (20 characters)</h3>
         <p id="access-key" />&nbsp;</p>
         <h3>Secret Access Key (40 characters)</h3>
         <p id="secret-key" />&nbsp;</p>
         <h3>Bucket Name (required)</h3>
         <p id="bucket">&nbsp;</p>
         <div>
           <button type="button" id="edit" class="btn btn-primary">
             <i class="fa fa-pencil"></i> Edit
           </button>
           <button type="button" id="save" class="btn btn-primary disabled hidden">
             <i class="fa fa-download"></i> Save
           </button>
           <button type="button" id="cancel" class="btn btn-primary hidden">
             <i class="fa fa-times"></i> Cancel
           </button>
         </div>
         </form>
      </section>
    </section>
  </section>
</section>

<script src="/app/module/palette/js/vendor/require.js" data-main="/app/module/palette/js/s3.js">
</script>
