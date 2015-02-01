<!DOCTYPE html>
<html>
<head>
  <title>Palette | Setup</title>
  <%include file="favicon.mako" />

  <meta charset="utf-8" />
  <meta name="viewport" content="width=1000,minimal-ui" />
  <meta name="apple-mobile-web-app-capable" content="yes" />
  <link rel="stylesheet" type="text/css" href="/app/module/palette/css/bootstrap.min.css" />
  <link rel="stylesheet" type="text/css" href="/app/module/palette/css/font-awesome.min.css" />
  <link rel="stylesheet" type="text/css" href="/app/module/palette/fonts/fonts.css" />
  <link rel="stylesheet" type="text/css" href="/app/module/palette/css/style.css" media="screen" />

  <script>
  var require = {
    paths: {
      'jquery': '/app/module/palette/js/vendor/jquery',
      'topic': '/app/module/palette/js/vendor/pubsub',
      'template' : '/app/module/palette/js/vendor/mustache',
      'domReady': '/app/module/palette/js/vendor/domReady',

      'bootstrap': '/app/module/palette/js/vendor/bootstrap',
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
  <div class="center-container error-page hidden">
    <p>HTTPS(443) on licensing.palette-software.com is not reachable.  This error must be fixed immediately.</p>
  </div>
  <div class="center-container configuration setup-page initial">

    <!-- top-zone? -->
    <section>
      <h1>Welcome to Palette Software Server Setup</h1>
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
      <h2>Palette License Key</h2>
      <p>Please enter your License Key below.</p>
      <input type="text" id="license-key" />
    </section>
    <hr />
    <section id="admin">
      <%include file="config/admin.mako" />
    </section>
    <hr />
    <section id="mail">
      <%include file="config/mail.mako" />
    </section>
    <hr />
    <section id="ssl">
      <%include file="config/ssl.mako" />
    </section>
    <button type="button" id="save" class="btn btn-primary disabled">
      Save Setting
    </button>
  </div>

  <%include file="dropdown.mako" />
  <%include file="onoff.mako" />

  <script src="/app/module/palette/js/vendor/require.js"
          data-main="/app/module/palette/js/initial.js" >
  </script>
</body>
</html>
