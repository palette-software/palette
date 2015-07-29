# -*- coding: utf-8 -*-
<%inherit file="layout.mako" />

<%block name="title">
<title>About Palette</title>
</%block>

<div class="dynamic-content about-page">
  <div class="scrollable">
    <h1 class="page-title">About Palette</h1>

    <h2>Version ${obj.version}</h2>
    <div>
      <p>&copy; 2015 Palette Software</p>
      %if obj.license_key:
      <p>License Key: ${obj.license_key}</p>
      %endif
      <p>The use of this product is subject to the terms of the <a href="http://kb.palette-software.com/palette-end-user-license-agreement">Palette End User Agreement</a>, unless otherwise specified therein.</p>
    </div>

    <h2>Palette Software</h2>
    <div class="address">
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
    
    <div>
      <h2>Palette Support</h2>
      <p>Enable or Disable Palette's Built-in support communication</p>
      <p class="slider-group">
        <span>Enable Support
          <span id="enable-support" class="onoffswitch yesno"
                data-href="/rest/about/support"></span>
        </span>
      </p>
    </div>
    %endif
  </div>
</section>

<script src="/js/vendor/require.js" data-main="/js/about.js">
</script>
