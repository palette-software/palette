# -*- coding: utf-8 -*-
<%inherit file="layout.mako" />

<%block name="title">
<title>Palette | Welcome</title>
</%block>

<body>
  <div class="container-vcenter">
    <div class="login-box">
      <a href="/">
        <img class="login" src="/images/palette_logo.png">
      </a>
      <form method="POST" action="/login/authenticate" id="form" class="form-group">
        <label for="username" class="control-label">Tableau Server Username</label>
        <input type="text" name="username" id="username" class="form-control" />
        <label for="password" class="control-label">Tableau Server Password</label>
        <input type="password" name="password" id="password" class="form-control"/>
        <section class="row">
          <section class="col-xs-12">
            <button id="login">Login</button>
          </section>
        </section>
      </form>
      <p class="hidden error" id="error">
        <b>Unrecognized Username or Password</b>
      </p>
      <p>If you forgot your Tableau Server Username or Password,<br/>please contact your organization's Tableau Server Administrator.</p>
    </div>
  </div>

  <script src="/js/vendor/require.js" data-main="/js/login.js" >
  </script>
</body>
