<nav id="mainNav" data-topbar>
  <div class="container">
    <a class="site-id" href="/"></a>
    <span id="toggle-main-menu" class="fi-list"></span>
    <ul class="nav">
      <li class="more">
        <a class="help" href="javascript:void(0)">
          <i class="fa fa-question-circle"></i>
          <span>Help</span>
        </a>
        <ul>
          <li>
            <a href="http://hello.palette-software.com/hc/en-us/requests" target="_blank">
              <i class="fa fa-fw fa-envelope"></i> My Support Requests
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
          <span>${req.remote_user.friendly_name}</span>
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
