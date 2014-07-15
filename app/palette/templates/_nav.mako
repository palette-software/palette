<nav id="mainNav" data-topbar>
  <div class="container">
    <a class="site-id" href="/"></a>
    <span id="toggle-main-menu" class="fi-list"></span>
    <ul class="nav">
      <li class="more">
        <a class="help"><i class="fa fa-question-circle"></i>
          <span>Help</span>
	    </a>
        <ul>
          <li>
            <a class="help" href="javascript:void(0)">
              <i class="fa fa-fw fa-envelope"></i> Contact Palette
            </a>
          </li>
          <li>
            <a href="http://www.tableausoftware.com/support/help">
              <i class="fa fa-fw fa-book"></i> Tableau Docs
            </a>
          </li>
          <li>
            <a href="/support/about">
              <i class="fa fa-fw fa-info-circle"></i> About Palette
            </a>
          </li>
        </ul>
      </li>

      <li class="more">
        <a id="profile-link" href="/profile">
          <i class="fa fa-user"></i> 
          <span>${req.remote_user.friendly_name}
%if req.remote_user.roleid > req.remote_user.role.NO_ADMIN:
          (${req.remote_user.role.name})</span>
%else:
          </span>
%endif

        </a>
        <ul>
          <li>
            <a href="/profile">
              <i class="fa fa-fw fa-user"></i> Edit Profile
            </a>
          </li>
          <li>
            <a href="/logout">
              <i class="fa fa-fw fa-sign-out"></i> Log out
            </a>
          </li>
        </ul>
      </li>
    </ul>
  </div>
</nav>

<script src="/app/module/palette/js/contact.js"></script>
