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
<meta name="viewport" content="width=900, minimal-ui">
<meta name="apple-mobile-web-app-capable" content="yes">
<link rel="stylesheet" type="text/css" href="/app/module/palette/fonts/fonts.css" media="screen">
<link rel="stylesheet" type="text/css" href="/app/module/palette/css/style.css" media="screen">

<script src="/app/module/palette/js/vendor/require.js"
        data-main="/app/module/palette/js/login.js" >
</script>
</%block>

</head>
<body class="full-size-box">
  <section class="login-box">
    <div class="center-box">
      <a href="/">
        <img class="login" src="/app/module/palette/images/palette_logo.png">
      </a>
      <form method="POST" action="/login" id="form">
        <div class="login-label">Tableau Server Username</div>
        <input class="login" type="text" name="username" id="username">
        <div class="login-spacer"></div>
        <div class="login-label">Tableau Server Password</div>
        <input class="login" type="password" name="password" id="password">
        <section class="row">
          <section class="col-xs-12">
            <button type="submit" name="login" id="login"
                    class="login">Login
            </button>
          </section>
        </section>
        %if 'AUTH_ERROR' in req.environ:
        <section class="hidden" id="auth-error"></section>
        %endif
        <p class="hidden error" id="error">
          <b>Unrecognized Username or Password</b>
        </p>
        <p class="login-instructions">If you forgot your Tableau Server Username or Password, please contact your organization's Tableau Server Administrator.</p>
      </form>
    </div>
  </section>
</body>
</html>
