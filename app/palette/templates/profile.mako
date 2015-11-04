# -*- coding: utf-8 -*-
<%inherit file="webapp.mako" />

<%block name="title">
<title>Palette - Profile</title>
</%block>

<div class="content profile-page">
  <div>
    <div class="top-zone">
      <h1>Profile</h1>
    </div>

    <div class="bottom-zone">
      <h2>Tableau Server Display Name</h2>
      <p>${req.remote_user.friendly_name}</p>

      <h2>Tableau Server Username</h2>
      <p>${req.remote_user.name}</p>

      <h2>Email</h2>
      <p>${req.remote_user.email or ''}</p>

      %if req.remote_user.userid > 0:
      <h2>Tableau Server User License</h2>
      <p>Interactor</p>

      <h2>Tableau Server Administrator Role</h2>
      <p>System Administrator</p>

      <h2>Tableau Server User Publisher Role</h2>
      <p>Publisher</p>
      %endif

      <h2>Palette Role</h2>
      <p>${req.remote_user.display_role()}</p>

      <h2>Email Notifications</h2>
      <div class="onoffswitch"
           data-name="${req.remote_user.name}"
           data-href="/rest/users/email-level">
        ${req.remote_user.email_level}
      </div>
    </div> <!-- bottom-zone -->
  </div>
</div> <!-- content -->

<script src="/js/vendor/require.js" data-main="/js/profile.js">
</script>
