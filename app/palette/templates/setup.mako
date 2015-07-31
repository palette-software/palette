<!DOCTYPE html>
<html>
<head>
  <title>Palette | Setup</title>
  <%include file="favicon.mako" />

  <meta charset="utf-8" />
  <meta name="viewport" content="width=1000,minimal-ui" />
  <meta name="apple-mobile-web-app-capable" content="yes" />
  <link rel="stylesheet" type="text/css" href="/css/bootstrap.min.css" />
  <link rel="stylesheet" type="text/css" href="/css/font-awesome.min.css" />
  <link rel="stylesheet" type="text/css" href="/fonts/fonts.css" />
  <link rel="stylesheet" type="text/css" href="/css/style.css" media="screen" />

  <!-- FIXME: merge with layout.mako -->
  <script>
  var require = {
    paths: {
      'jquery': '/js/vendor/jquery',
      'topic': '/js/vendor/pubsub',
      'template' : '/js/vendor/mustache',
      'domReady': '/js/vendor/domReady',

      'bootstrap': '/js/vendor/bootstrap',
      'lightbox': '//www.helpdocsonline.com/v2/lightbox'
    },
    shim: {
      'bootstrap': {
         deps: ['jquery']
      },
      'lightbox': {
         deps: ['jquery']
      }
    }
  };
  </script>

</head>

<body class="scrollable">
  <nav class="navbar">
    <div class="navbar-header"></div>
  </nav>
  <div class="center-container licensing status initial hidden">
    <h1>Prepare<br/>for<br/>Awesomeness!
    <span id="wrap">
      <div class="dot"></div>
      <div class="dot"></div>
      <div class="dot"></div>
    </span>
    </h1>
    <p>We are trying to Contact Palette License Server licensing.palette-software.com on HTTPS port 443.</p>
  </div>
  <div class="center-container licensing error initial hidden">
    <h2 class="error">
      <span class="fa-stack">
        <i class="fa fa-fw fa-stack-1x fa-times-circle red"></i>
      </span>
      Failed to Contact Palette License Server</h2>
    <p>This Palette Server failed to contact Palette Licensing at licensing.palette-software.com on HTTPS port 443.</p>
    <p>Palette Server must be able to communicate with Palette Licensing in order to verify the validity of your Palette License.</p>
    <p>The cause of this error is likely to be your <i>firewall settings</i>. Please be sure your settings meet our <a href="http://kb.palette-software.com/network-configuration">Network Configuration Requirements</a>.</p>
    <p>This Palette Server will continue to attempt to connect to Palette Licensing every few seconds. Once the firewall settings are correct you will no longer see this message.</p>
    <p>If this message persists, please contact Palette Support at <a href="mailto:support@palette-software.com">support@palette-software.com</a>.
    </p>
  </div>
  <div class="center-container configuration setup-page initial hidden">
    <section class="top-zone">
      <h1 class="page-title">Welcome to Palette Server Setup</h1>
      <p>Please set up your Mail, Hostname and SSL Certificate Settings for your Palette Server</p>
    </section>

    <section>
      <%include file="config/server-url.mako" />
    </section>
    <hr />
    <section>
      <%include file="config/tableau-server-url.mako" />
    </section>
    <hr />
    <section>
      <a id="237795" href="#"><i class="fa fa-question-circle help"></i></a>
      <h2>Palette License Key *</h2>
      <p>Your 32 digit Palette License Key is found in the confirmation email</p>
      <input type="text" id="license-key" />
    </section>
    <hr />
    <section id="admin">
      <a id="236536" href="#"><i class="fa fa-question-circle help"></i></a>
      <h2>Palette Server Admin Credentials</h2>
      <p>Create a password for the built-in "Palette" username</p>
      <p>Any combination of 8+ case-sensitive, alphanumeric characters (i.e. A-Z, a-z, 0-9, and !,@,#,$,%)</p>
      <label for="password">Password *</label>
      <input type="password" id="password" />
      <label for="confirm-password">Confirm Password *</label>
      <input type="password" id="confirm-password" />
    </section>
    <hr />
    <section id="mail">
      <%include file="config/mail.mako" />
    </section>
    <hr />
    <section id="tz">
      <%include file="config/tz.mako" />
    </section>
    <hr />
    <section class="bottom-zone">
      <button type="button" id="save" class="btn btn-primary">
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
</html>
