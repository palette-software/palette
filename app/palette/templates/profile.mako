# -*- coding: utf-8 -*-
<%inherit file="configure.mako" />

<%block name="title">
<title>Palette - Profile</title>
</%block>

<section class="dynamic-content config-content">
  <section class="top-zone">
    <h1 class="page-title">Profile</h1>
  </section>
  <section class="row bottom-zone">
    <section class="col-sm-12 col-md-8">
      <label class="profile-page">Tableau Server Display Name</label>
      <p id="friendly"></p>
      <label class="profile-page">Tableau Server Username</label>
      <p id="username"></p>
      <label class="profile-page">Email</label>
      <p><span id="email"></span> 
        <a href="#"><i class="fa fa-fw fa-pencil"></i></a>
      </p>
      <label class="profile-page">Tableau Server User License</label>
      <p id="user-license"></p>
      <label class="profile-page">Tableau Server Administrator Role</label>
      <p id="user-administrator-role"></p>
      <label class="profile-page">Tableau Server User Publisher Role</label>
      <p id="user-publisher-role"></p>
      </div>
      <section class="row margin-top">
        <section class="col-xs-12 col-sm-6">
          <button type="submit" name="save" class="p-btn">Save</button>
        </section>
      </section>
    </section>
  </section>
</section>

<script src="/app/module/palette/js/vendor/require.js" data-main="/app/module/palette/js/profile.js">
</script>
