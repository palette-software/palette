<!DOCTYPE html>
<html>
<head>

<%block name="title">
<title>Palette | Welcome</title>
</%block>

<%block name="favicon">
<%include file="favicon.mako" />
</%block>

<%block name="fullstyle">
<meta charset="utf-8">
<meta name="viewport" content="initial-scale=1, maximum-scale=1, user-scalable=no, width=device-width">
<link href='http://fonts.googleapis.com/css?family=Roboto:300,500' rel='stylesheet' type='text/css'>
<link rel="stylesheet" type="text/css" href="/app/module/palette/css/foundation.css">
<link rel="stylesheet" type="text/css" href="/app/module/palette/css/foundation-icons.css">
<link rel="stylesheet" type="text/css" href="/app/module/palette/css/normalize.css" media="screen">
<link rel="stylesheet" type="text/css" href="/app/module/palette/css/style.css" media="screen">

<script src="/app/module/palette/js/vendor/modernizr.js"></script>
</%block>

</head>
<body>

  <script src="//ajax.googleapis.com/ajax/libs/dojo/1.9.0/dojo/dojo.js"></script>

    <section class="full-size-box">
      <section class="login-box">
        <a href="/"><img src="/app/module/palette/images/palette_logo_600dpi-3.png"></a>
        <form method="post" action="/login" id="form">
          <p>
            <label>Username</label>
            <input type="text" name="username" id="username">
          </p>
          <p>
            <label>Password</label>
            <input type="password" name="password" id="password">
          </p>
          <ul class=" col-sm-block-grid-1">
              <li><button type="submit" name="login" id="login" class="p-btn p-btn-grey">Login</button></li>
            </ul>
          <p class="text-center text-small">
            <a href="/forgot">I forgot my username and/or password</a>
          </p>
          %if 'AUTH_ERROR' in req.environ:
          <section class="hidden" id="auth-error"></section>
          %endif
          <p class="hidden error" id="error">
            Login Failed <b>Invalid userID</b> or <b>password</b>
          </p>
        </form>
      </section>
    <script>
      require({
      packages: [
      { name: "akiri", location: "/app/module/akiri.framework/js" }
      ]
      }, [ "akiri/login" ]);
    </script>
  </section>        
</body>
</html>
