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
          <input class="login" type="text" name="username" id="username"
            placeholder="Tableau Server Username">
          <input class="login" type="password" name="password" id="password"
            placeholder="Tableau Server Password">
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
          Login Failed <b>Invalid userID</b> or <b>password</b>
        </p>
      </form>
    </div>
  </section>
</body>
</html>
