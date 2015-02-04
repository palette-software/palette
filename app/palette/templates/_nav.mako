<nav id="mainNav" data-topbar>
  <div class="container">
    <a class="site-id" href="/"></a>
    <span class="message"></span>
    <ul class="nav">
      <li class="buy hidden">
        <a href="javascript:void(0)">Buy Now</a>
      </li>
      <li class="more">
        <a class="help" href="javascript:void(0)">
          <i class="fa fa-question-circle"></i>
          <span>Help</span>
        </a>
        <ul>
          <li>
            <a href="http://kb.palette-software.com" target="_blank">
              Knowledge Base
            </a>
          </li>
          <li>
            <a href="http://hello.palette-software.com/hc/en-us/requests" target="_blank">
              Support Requests
            </a>
          </li>
          <li>
            <a href="/support/about">
              About Palette
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
              My Profile
            </a>
          </li>
          <li>
            <a href="/logout">
              Log out
            </a>
          </li>
        </ul>
      </li>
    </ul>
  </div>
</nav>
