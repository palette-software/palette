# -*- coding: utf-8 -*-
<%inherit file="layout.mako" />

<%block name="title">
<title>Palette - Profile</title>
</%block>

<section class="dynamic-content">
  <h1 class="page-title">Profile</h1>
  <label class="profile-page">Tableau Server Display Name</label>
  <p>${req.remote_user.friendly_name}</p>
  <label class="profile-page">Tableau Server Username</label>
  <p>${req.remote_user.name}</p>
  <label class="profile-page">Email</label>
  <p class="editbox" data-href="/rest/profile/email">
    ${req.remote_user.email or ''}
  </p>
  <label class="profile-page">Tableau Server User License</label>
  <p>Interactor</p>
  <label class="profile-page">Tableau Server Administrator Role</label>
  <p>System Administrator</p>
  <label class="profile-page">Tableau Server User Publisher Role</label>
  <p>Publisher</p>
</section>

<script id="editbox-view" type="x-tmpl-mustache">
  <span>{{value}}</span>
  <i class="fa fa-fw fa-pencil"></i>
</script>

<script id="editbox-edit" type="x-tmpl-mustache">
  <input value="{{value}}" />
  <i class="fa fa-fw fa-check ok"></i>
  <i class="fa fa-fw fa-times cancel"></i>
</script>

<script src="/app/module/palette/js/vendor/require.js" data-main="/app/module/palette/js/profile.js">
</script>
