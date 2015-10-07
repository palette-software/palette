# -*- coding: utf-8 -*-
<%inherit file="layout.mako" />

<body>
  <nav class="navbar">
    <div class="navbar-header">
      <a class="navbar-brand" href="/"></a>
    </div>
  </nav>
  <div class="container initial hidden" id="licensing-status">
    <h1>Prepare<br/>for<br/>Awesomeness!
    <span id="wrap">
      <div class="dot"></div>
      <div class="dot"></div>
      <div class="dot"></div>
    </span>
    </h1>
    <p>We are trying to Contact Palette License Server licensing.palette-software.com on HTTPS port 443.</p>
  </div>
  <div class="container initial hidden" id="licensing-error">
    <h2>
      <span class="fa-stack">
        <i class="fa fa-fw fa-stack-1x fa-times-circle red"></i>
      </span>
      Failed to Contact Palette License Server</h2>
    <p>This Palette Server failed to contact Palette Licensing at licensing.palette-software.com on HTTPS port 443.  This is how Palette verifies the validity of your license.  Palette is inaccessible until this communication is possible.</p>
    <p>To help you troubleshoot, start with the most common blockers: HTTPS Proxy Server and Firewall Settings.</p>

    <h3>HTTP Proxy Server URL</h3>
    <p>If you use a HTTPS proxy server, input the URL here.  The URL must contain the protocol (e.g. http, https, etc.) For example: https://yourproxyserverurl.com</p>

    <div class="proxy">
      <input type="text" id="proxy-https" />
      <button id="connect">Connect</button>
    </div>

    <h3>Filewall Settings</h3>
    <p>Next, check that your firewall settings meet the <a href="http://kb.palette-software.com/network-configuration">Network Configuration Requirements</a>.</p>
    <p>If your settings are correct and this message persists, please contact Palette Support at <a href="mailto:support@palette-software.com">support@palette-software.com</a>.
    </p>
  </div>
  <div class="container configuration setup-page initial hidden">
    <section class="top-zone">
      <h1>Welcome to Palette Server Setup</h1>
      <p>Please configure your Palette Server.</p>
    </section>

%if req.platform.product != req.platform.PRODUCT_PRO:
    <section>
      <%include file="config/server-url.mako" />
    </section>
    <hr />
%endif
    <section>
      <%include file="config/tableau-server-url.mako" />
    </section>
    <hr />
%if req.platform.product != req.platform.PRODUCT_PRO:
    <section>
      <a id="237795" href="#"><i class="fa fa-question-circle help"></i></a>
      <h2>Palette License Key *</h2>
      <p>Your 32 digit Palette License Key is found in the confirmation email.</p>
      <input type="text" id="license-key" />
    </section>
    <hr />
%endif
    <section id="admin">
      <a id="236536" href="#"><i class="fa fa-question-circle help"></i></a>
      <h2>Palette Server Admin Credentials</h2>
      <p>Create a password for the built-in "Palette" username.</p>
      <p>Any combination of 8+ case-sensitive, alphanumeric characters (i.e. A-Z, a-z, 0-9, and !,@,#,$,%).</p>
      <label for="password">Password *</label>
      <input type="password" id="password" />
      <label for="confirm-password">Confirm Password *</label>
      <input type="password" id="confirm-password" />
    </section>
%if req.platform.product != req.platform.PRODUCT_PRO:
    <hr />
    <section id="mail">
      <%include file="config/mail.mako" />
    </section>
%endif
    <hr />
    <section id="tz">
      <%include file="config/tz.mako" />
    </section>
    <hr />
    <section class="bottom-zone">
      <button type="button" id="save" class="action">
        Save Settings
      </button>
    </section>
    <div class="version"></div>
  </div>

  <%include file="dropdown.mako" />
  <%include file="onoff.mako" />

  <script src="/js/vendor/require.js" data-main="/js/initial.js" >
  </script>
</body>
