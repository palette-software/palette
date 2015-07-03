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
      <a id="237795" href="#"><i class="fa fa-question-circle help"></i></a>
      <h2>Palette License Key *</h2>
      <p>Your 32 digit Palette License Key is found in the confirmation email</p>
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
    <hr />
    <section id="tz">
      <%include file="config/tz.mako" />
    </section>
    <button type="button" id="save" class="btn btn-primary disabled">
      Save Setting
    </button>
  </div>

  <%include file="dropdown.mako" />
  <%include file="onoff.mako" />

  <script src="/js/vendor/require.js" data-main="/js/initial.js" >
  </script>
</body>
</html>
