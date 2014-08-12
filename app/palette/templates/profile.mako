# -*- coding: utf-8 -*-
<%inherit file="layout.mako" />

<%block name="title">
<title>Palette - Profile</title>
</%block>

<section class="dynamic-content profile-page">
  <h1 class="page-title">Profile</h1>

  <h2>Tableau Server Display Name</h2>
  <p>${req.remote_user.friendly_name}</p>

  <h2>Tableau Server Username</h2>
  <p>${req.remote_user.name}</p>

  <h2>Email</h2>
  <p class="editbox"
     data-name="${req.remote_user.name}" data-href="/rest/users/email">
    ${req.remote_user.email or ''}
  </p>

%if req.remote_user.userid > 0:
  <h2>Tableau Server User License</h2>
  <p>Interactor</p>

  <h2>Tableau Server Administrator Role</h2>
  <p>System Administrator</p>

  <h2>Tableau Server User Publisher Role</h2>
  <p>Publisher</p>
%endif
</section>

<script src="/app/module/palette/js/vendor/require.js" data-main="/app/module/palette/js/profile.js">
</script>
