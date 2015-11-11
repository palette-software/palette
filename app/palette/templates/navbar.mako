# -*- coding: utf-8 -*-
<div class="navbar-announcement">
  TRIAL STATUS: <span class="trial-status"></span>
  <div class="trial-subscribe">
    <a target="_blank">SUBSCRIBE NOW</a>
  </div>
</div>
<nav class="navbar navbar-default">
  <div class="container-fluid">
    <div class="navbar-header">
      <a class="navbar-brand" href="/"></a>
    </div>

    <div class="navbar-collapse">
    <ul class="nav navbar-nav">
%if req.remote_user.roleid > req.remote_user.role.READONLY_ADMIN:
      <li class="dropdown">
        <i class="config-menu" data-toggle="dropdown" role="button"
           aria-haspopup="true" aria-expanded="false">
        </i>
        <ul class="dropdown-menu">
          <li><a href="/configure/setup">Setup Palette</a></li>
            <li><a href="/configure/general">General Configuration</a></li>
            <li><a href="/configure/users">Users</a></li>
            <li><a href="/configure/machines">Machines</a></li>
            <li><a href="/configure/yml">Tableau Settings</a></li>
          </ul>
      </li>
%endif
      <li class="dropdown">
        <i class="help-menu" data-toggle="dropdown" role="button"
           aria-haspopup="true" aria-expanded="false">
        </i>
        <ul class="dropdown-menu">
          <li>
            <a href="http://kb.palette-software.com" target="_blank">
              Knowledge Base
            </a>
          </li>
          <li>
            <a href="http://hello.palette-software.com/hc/en-us/requests"
               target="_blank">
              Support Requests
            </a>
          </li>
          <li>
            <a href="/support/about">About Palette</a>
          </li>
          <li>
            <a href="http://www.palette-software.com/agent" target="_blank">
              Download Palette Agent
            </a>
          </li>
        </ul>
      </li>
      <li class="dropdown">
        <div data-toggle="dropdown" role="button"
           aria-haspopup="true" aria-expanded="false">
          <i class="user-menu"></i>
          <span>${req.remote_user.friendly_name}</span>
        </div>
        <ul class="dropdown-menu">
          <li><a href="/profile">My Profile</a></li>
          <li><a href="/logout">Log out</a>
          </li>
        </ul>
      </li>
    </ul>
    </div>
  </div>
</nav>
