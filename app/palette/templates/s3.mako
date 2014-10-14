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
           <h3>Access Key ID</h3>
           <input type="text" id="access-key" />
           <label for="access-key">&nbsp;</label>
           <h3>Secret Access Key</h3>
           <input type="password" id="secret-key" />
           <label for="secret-key">&nbsp;</label>
           <h3>S3 URL or Bucket Name</h3>
           <input type="text" id="url" />
           <div>
             <button type="button" id="save" class="btn btn-primary disabled">
               Save
             </button>
             <button type="button" id="cancel" class="btn btn-primary">
               Cancel
             </button>
             <button type="button" id="delete" class="btn btn-primary okcancel"
                     data-text="Are you sure you want to delete the S3 credentials?">
               Delete
             </button>
           </div>
         </form>
      </section>
    </section>
  </section>
</section>

<script src="/app/module/palette/js/vendor/require.js" data-main="/app/module/palette/js/s3.js">
</script>
