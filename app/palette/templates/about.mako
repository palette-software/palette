# -*- coding: utf-8 -*-
<%inherit file="layout.mako" />

<%block name="title">
<title>About Palette</title>
</%block>

<section class="dynamic-content about-page">
  <h1 class="page-title">About Palette</h1>

  <h2>Version ${obj.version}</h2>
  <div>
    <p>&copy; 2014 Palette Software</p>
%if obj.license_key:
    <p>License Key: ${obj.license_key}</p>
%endif
    <p>The use of this product is subject to the terms of the Palette End User Agreement, unless otherwise specified therein.</p>
  </div>

  <h2>Palette Software</h2>
  <div>
    <p>156 2nd Street</p>
    <p>San Francisco, California 94105</p>
  </div>

  <h2>Contact</h2>
  <div>
    <p><a href='mailto:hello@palette-software.com'>hello@palette-software.com</a></p>
    <p><a target='_blank' href='http://www.palette-software.com'>www.palette-software.com</a></p>
  </div>

%if req.remote_user.roleid > req.remote_user.role.READONLY_ADMIN:
  <div>
     <button type="button" id="restart-webserver"
             class="btn btn-primary okcancel"
             data-text="Are you sure you want to restart the webserver?">
       Restart Webserver
     </button>
     <button type="button" id="restart-controller"
             class="btn btn-primary okcancel"
             data-text="Are you sure you want to restart the controller?">
       Restart Controller
     </button>
  </div>
%endif
</section>

<script src="/app/module/palette/js/vendor/require.js" data-main="/app/module/palette/js/about.js">
</script>
</html>


