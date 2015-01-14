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
      <!-- top-zone? -->
      <section>
	<h1>Welcome to Palette Software Server Setup</h1>
	<p>Please set up your Mail, Hostname and SSL Certificate Settings for your Palette Server</p>
	<hr />
      </section>
      <section>
	<h3>Password *</h3>
	<input type="password" id="password" />
	<!--<label for="password">&nbsp;</label>-->
	<h3>Confirm Password *</h3>
	<input type="password" id="confirm-password" />
	<!--<label for="confirm-password">&nbsp;</label>-->
      </section>
      <hr />
      <section>
	<%include file="config/mail.mako" />
      </section>
      <hr />
      <section>
	<button type="button" id="save" class="btn btn-primary disabled">
	  Save
	</button>
	<button type="button" id="cancel" class="btn btn-primary">
	  Cancel
	</button>
      </section>
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
          data-main="/app/module/palette/js/initial.js" >
  </script>
</body>
</html>
