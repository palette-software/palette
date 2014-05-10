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
      <label class="profile-page">Tableau Server Friendly Name</label>
      <input type="text" name="friendly" placeholder="Friendly Name" />
      <label class="profile-page">Tableau Server Username</label>
      <input type="email" name="username" placeholder="Tableau Username" />
      <label class="profile-page">Email</label>
      <input type="email" name="email" placeholder="Email Name" />
      <label class="profile-page">Tableau Server User License</label>
      <input type="text" name="user-license" placeholder="User License Type" />
      <label class="profile-page">Tableau Server Administrator Role</label>
      <input type="text" name="user-administrator-role" placeholder="User Administrator Role" />
      <label class="profile-page">Tableau Server User Publisher Role</label>
      <input type="text" name="user-publisher-role" placeholder="User Publisher Role" />
      </div>
      <section class="row margin-top">
        <section class="col-xs-12 col-sm-6">
          <button type="submit" name="save" class="p-btn p-btn-grey">Save</button>
        </section>
        <section class="col-xs-12 col-sm-6">
          <!-- ONLY SHOW AFTER SAVE IS PRESSED <button type="submit" name="revert" class="p-btn p-btn-grey"><span class="fi-refresh"></span> Revert</button>
               </section>-->
        </section>
      </section>
    </section>
  </section>
</section>

<script src="/app/module/palette/js/vendor/require.js" data-main="/app/module/palette/js/profile.js">
</script>
