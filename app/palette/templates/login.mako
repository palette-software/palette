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
<link rel="stylesheet" type="text/css" href="/fonts/fonts.css" media="screen">
<link rel="stylesheet" type="text/css" href="/css/style.css" media="screen">

<script src="/js/vendor/require.js" data-main="/js/login.js" >
</script>
</%block>

</head>
<body class="full-size-box">
  <section class="login-box">
    <div>
      <a href="/">
        <img class="login" src="/images/palette_logo.png">
      </a>
      <form method="POST" action="/login/authenticate" id="form">
        <label for="username">Tableau Server Username</label>
        <input type="text" name="username" id="username">
        <label for="password">Tableau Server Password</label>
        <input type="password" name="password" id="password">
        <section class="row">
          <section class="col-xs-12">
            <button class="btn btn-primary" type="submit" name="login" id="login">
              Login
            </button>
          </section>
        </section>
        <input type="hidden" id="redirect" name="redirect" value=""/>
      </form>
      %if 'AUTH_ERROR' in req.environ:
      <section class="hidden" id="auth-error"></section>
      %endif
      <p class="hidden error" id="error">
        <b>Unrecognized Username or Password</b>
      </p>
    </div>
    <p>If you forgot your Tableau Server Username or Password,<br/>please contact your organization's Tableau Server Administrator.</p>
  </section>
</body>
</html>
