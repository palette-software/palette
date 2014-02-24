<!DOCTYPE html>
<html>
<head>

<%block name="title">
<title>Palette</title>
</%block>

<%block name="favicon">
<%include file="favicon.mako" />
</%block>

<%block name="fullstyle">
<link rel="stylesheet" type="text/css" href="/app/module/akiri.framework/css/style.css" media="screen">
<link href="http://fonts.googleapis.com/css?family=Roboto:300,400,700|Lato:100,300,400" rel="stylesheet" type="text/css">
<link rel="stylesheet" type="text/css" href="/app/module/palette/css/style.css" media="screen">
<%block name="style"></%block>
</%block>

</head>
<body>
  <nav id="mainNav">
    <div class="container">
      <%include file="_logo.mako" />
      <ul id="nav">
        <li id="help"><a href="#">Help<span class="arrow-down"></span></a></li>
    </div>
  </nav>

  <script src="//ajax.googleapis.com/ajax/libs/dojo/1.9.0/dojo/dojo.js"></script>

  <div class="wrapper">
    <div class="container">
      <div class="box">
        <form method="post" action="/login" id="form">
          <h1>Login</h1>
          %if 'AUTH_ERROR' in req.environ:
          <div class="hidden" id="auth-error"></div>
          %endif
          <p class="hidden error" id="error">
            Login failed; <b>Invalid userID</b> or <b>password</b>
          </p>
          <p>
            <input type="text" name="username" id="username"
                   placeholder="Username">
          </p>
          <p>
            <input type="password" name="password" id="password"
                   placeholder="Password">
          </p>
          <p class="right nopad">
            <input type="submit" value="Login"
                   name="login" id="login" class="login">
          </p>
        </form>
      </div>
    </div>
    <script>
      require({
      packages: [
      { name: "akiri", location: "/app/module/akiri.framework/js" }
      ]
      }, [ "akiri/login" ]);
    </script>
  </div>        
</body>
</html>
