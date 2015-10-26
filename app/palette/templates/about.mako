# -*- coding: utf-8 -*-
<%inherit file="webapp.mako" />

<%block name="title">
<title>About Palette</title>
</%block>

<div class="dynamic-content about-page">
  <div class="scrollable">
    <div class="top-zone">
      <h1>About Palette</h1>
    </div> <!-- top-zone -->
    <div class="bottom-zone">
      <h3>Version <span id="version"></span></h3>
      <div>
        <p>&copy; 2015 Palette Software</p>
        <p>License Key: <span id="license-key"></span></p>
        <p>The use of this product is subject to the terms of the <a href="http://kb.palette-software.com/palette-end-user-license-agreement">Palette End User Agreement</a>, unless otherwise specified therein.</p>
      </div>

      <h3>Palette Software</h3>
      <div class="address">
        <p>156 2nd Street</p>
        <p>San Francisco, California 94105</p>
      </div>

      <h3>Contact</h3>
      <div>
        <p><a href='mailto:hello@palette-software.com'>hello@palette-software.com</a></p>
        <p><a target='_blank' href='http://www.palette-software.com'>www.palette-software.com</a></p>
      </div>

      %if req.platform.product != req.platform.PRODUCT_PRO:
      %if req.remote_user.roleid > req.remote_user.role.READONLY_ADMIN:

      <div>
        <hr />
        <h2>Palette Updates</h2>
        <p>Your Palette Server can update automatically outside of normal business hours or on-demand.  Updates usually take 5-10 minutes and do not affect historical continuity.  Palette Events will let you know that the update is complete.</p>
        <p>Note: Automatic Updates are recommended for the most reliable service.</p>
        <div class="slider-group">
          <div>
            <div>Automatic Updates</div>
            <span id="enable-updates" class="onoffswitch"
                  data-href="/rest/update"></span>
          </div>
        </div> <!-- slider-group -->
        <p>Turn on Automatic Palette Updates to stay up-to-date with the latest features (recommended).</p>

        <h3>Manual Updates</h3>
        <p>Update your Palette Server to the latest version, on-demand and on your schedule.</p>
        <button type="button" id="manual-update" class="action disabled"
                data-toggle="modal-popup"
                data-text="Update Palette Server to the latest available version now?">
          Update Now
        </button>
      </div>

      <div>
        <hr/>
        <h2>Palette Support</h2>
        <p>These features are available to minimize troubleshooting and should only be used by Palette Admins when engaging the Palette Support team.  For assistance, contact <a href='mailto:support@palette-software.com'>support@palette-software.com</a>.
        </p>
        <div class="slider-group">
          <div>
            <div>Palette Remote Support</div>
            <span id="enable-support" class="onoffswitch"
                  data-href="/rest/support"></span>
          </div>
        </div> <!-- slider-group -->
        <p>Turn on your Palette Server's remote communication for enhanced support from the Palette team.</p>

        <h3>Palette Webserver</h3>
        <p>Restart your Palette Webserver to reset the Web UI during support engagements.</p>
        <button type="button" id="restart-webserver" class="action disabled"
                data-toggle="modal-popup"
                data-text="Are you sure you want to restart the webserver?">
          Restart Webserver
        </button>

        <h3>Palette Controller</h3>
        <p>Restart your Palette Controller to reset the Server during support engagements.</p>
        <button type="button" id="restart-controller" class="action disabled"
                data-toggle="modal-popup"
                data-text="Are you sure you want to restart the controller?">
          Restart Controller
        </button>
      </div>
      
      %endif
      %endif
    </div> <!-- bottom-zone -->
  </div>
</section>

<script src="/js/vendor/require.js" data-main="/js/about.js">
</script>
