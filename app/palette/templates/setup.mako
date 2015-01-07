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

      'bootstrap': '/app/module/palette/js/vendor/bootstrap'
    },
    shim: {
      'bootstrap': {
         deps: ['jquery']
      }
    }
  };
  </script>

</head>

<body>
  <nav class="navbar">
    <div class="navbar-header"></div>
  </nav>
  <div class="main-container">
    <div class="center-block setup-page">
      <h1>Welcome to Palette Software Server Setup</h1>
      <p>Please set up your Mail, Hostname and SSL Certificate Settings for your Palette Server</p>
      <hr />
      <h3>Password *</h3>
      <input type="password" id="password" />
      <!--<label for="password">&nbsp;</label>-->
      <h3>Confirm Password *</h3>
      <input type="password" id="confirm-password" />
      <!--<label for="confirm-password">&nbsp;</label>-->
      <hr/>
      <div class="row">
	<div class="col-xs-6">
          <h3>Mail Server Type</h3>
	  <span id="mail-server-type" class="btn-group"></span>
        </div>
	<div class="col-xs-6">
	</div>
      </div>
      <div class="row">
        <div class="col-xs-6">
          <h3>Palette Alert Email Name</h3>
          <input type="text" id="alert-email-name" />
        </div>
        <div class="col-xs-6">
          <h3>Palette Alert Email Address</h3>
          <input type="text" id="alert-email-address" />
	</div>        
      </div>
      <div class="row">
        <div class="col-xs-6">
          <h3>SMTP Mail Server</h3>
          <input type="text" id="smtp-server" />
        </div>
        <div class="col-xs-6">
          <h3>Port</h3>
          <input type="text" id="smtp-port" />
	</div>
      </div>
      <div class="row">
        <div class="col-xs-6">
          <h3>SMTP Username</h3>
          <input type="text" id="smtp-username" />
        </div>
	<div class="col-xs-6">
          <h3>Enable TLS</h3>
          <div id="enable-tls" class="onoffswitch yesno"></div>
	</div>
      </div>
      <div class="row">
        <div class="col-xs-6">
          <h3>SMTP Password</h3>
          <input type="password" id="smtp-password" />
        </div>
	<div class="col-xs-6">
          <h3>Test Email Recipient</h3>
          <input type="text" id="test-email-recipient" />
          <button type="button" id="test" class="btn disabled">
            Test Email
          </button>
        </div>
      </div>
      <hr/>
      <div>
        <button type="button" id="save" class="btn btn-primary disabled">
          Save
        </button>
        <button type="button" id="cancel" class="btn btn-primary">
          Cancel
        </button>
      </div>
    </div>
  </div>

  <!-- FIXME: mako template, duplicate with general.mako -->
  <script id="dropdown-template" type="x-tmpl-mustache">
    <button type="button" class="btn btn-default dropdown-toggle" data-toggle="dropdown"><div data-id="{{id}}">{{value}}</div><span class="caret"></span>
    </button>
    <ul class="dropdown-menu" role="menu">
      {{#options}}
      <li><a data-id="{{id}}">{{option}}</a></li>
      {{/options}}
    </ul>
  </script>

   <!-- FIXME: mako template, duplicate with layout.mako -->
  <script id="onoffswitch" type="x-tmpl-mustache">
  <input type="checkbox" class="onoffswitch-checkbox" {{checked}}>
    <label class="onoffswitch-label">
      <span class="onoffswitch-inner"></span>
      <span class="onoffswitch-switch"></span>
    </label>
  </script>

  <script src="/app/module/palette/js/vendor/require.js"
          data-main="/app/module/palette/js/setup.js" >
  </script>
</body>
</html>
