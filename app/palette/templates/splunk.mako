# -*- coding: utf-8 -*-
<%inherit file="configure.mako" />

<%block name="title">
<title>Palette - Splunk Integration</title>
</%block>

<section class="dynamic-content config-content">
  <section class="top-zone">
    <h1 class="page-title">Splunk Integration</h1>
  </section>
  <section class="row bottom-zone">
    <section class="col-sm-12 col-md-8">
      <label class="profile-page">Splunk Server Address</label>
      <p>https://splunk.palette-software.com<a href="#"><i class="fa fa-fw fa-pencil"></i></a></p>
      <label class="profile-page">Splunk Port</label>
      <p>9997<a href="#"><i class="fa fa-fw fa-pencil"></i></a></p>
      <label class="profile-page">Splunk Administrator Username</label>
      <p>john<a href="#"><i class="fa fa-fw fa-pencil"></i></a>
      </p>
      <label class="profile-page">Splunk Password</label>
      <p>********<a href="#"><i class="fa fa-fw fa-pencil"></i></a></p>
    </section>
  </section>
</section>

<script src="/app/module/palette/js/vendor/require.js" data-main="/app/module/palette/js/splunk.js">
</script>
