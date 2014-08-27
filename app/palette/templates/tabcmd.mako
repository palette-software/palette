# -*- coding: utf-8 -*-
<%inherit file="layout.mako" />

<%block name="title">
<title>Palette - Tabcmd User Configuration</title>
</%block>

<section class="dynamic-content tabcmd-page">

  <h1 class="page-title">Tabcmd User</h1>
  <p>The Tableau Administrator user credentials used to manage the Palette Workbook Archive</p>

  <h2 class="page-subtitle">Primary Credentials</h2>
  <h2>Username</h2>
  <p class="editbox"
    data-href="/rest/workbooks/primary/user">
    ${req.primary_user}
  </p>
  <h2>Password</h2>
  <p class="editbox password"
    data-href="/rest/workbooks/primary/password">
    ${req.primary_pw}
  </p>

  <h2 class="page-subtitle">Secondary Credentials</h2>
  <h2>Username</h2>
  <p class="editbox"
    data-href="/rest/workbooks/secondary/user">
    ${req.secondary_user}
  </p>
  <h2>Password</h2>
  <p class="editbox password"
    data-href="/rest/workbooks/secondary/password">
    ${req.secondary_pw}
  </p>
  
</section>

<script src="/app/module/palette/js/vendor/require.js" data-main="/app/module/palette/js/tabcmd.js">
</script>
