# -*- coding: utf-8 -*-
<section class="main-side-bar">
  <section class="status">
    <span class="fa-stack">
      <i class="fa fa-circle fa-stack-1x"></i>
      <i id="status-icon" class="fa fa-fw fa-stack-1x ${obj.status_class}"></i>
    </span>
    <h1>STATUS</h1>
    <h3 id="status-text">${obj.status_text}</h3>
%if req.remote_user.roleid > req.remote_user.role.NO_ADMIN:
    <i class="fa fa-fw fa-angle-right" id="expand-right"></i>
%endif
  </section>
  <ul class="actions">
    <li ${obj.active=='home' and 'class="active"' or ''}>
      <a href="/">
        <i class="fa fa-fw fa-clock-o"></i><span>Events</span>
      </a>
    </li>
    <li class="category">
      <a href="/workbook/archive">
        <i class="fa fa-fw fa-copy"></i><span>Archive</span>
        <i class="fa fa-fw fa-angle-${obj.archive and 'up' or 'down'} expand"></i>
      </a>
      <ul ${obj.archive and 'class="visible"' or ''}>
        <li ${obj.active=='workbook-archive' and 'class="active"' or ''}>
          <a href="/workbook/archive">
            <i class="fa fa-fw"></i><span>Workbooks</span>
          </a>
        </li>
	<li ${obj.active=='datasource-archive' and 'class="active"' or ''}>
	  <a href="/datasource/archive">
            <i class="fa fa-fw"></i><span>Data Sources</span>
	  </a>
	</li>
      </ul>
    </li>
%if req.remote_user.roleid > req.remote_user.role.NO_ADMIN:
    <li class="has-side-bar ${obj.active=='manage' and 'active' or ''}">
      <a href="/manage">
        <i class="fa fa-fw fa-wrench"></i><span>Manage Tableau</span>
      </a>
    </li>
    <li class="category">
      <a>
        <i class="fa fa-fw fa-cog"></i><span>Configuration</span>
        <i class="fa fa-fw fa-angle-${obj.expanded and 'up' or 'down'} expand"></i>
      </a>
      <ul ${obj.expanded and 'class="visible"' or ''}>
%if req.remote_user.roleid > req.remote_user.role.READONLY_ADMIN:
        <li ${obj.active=='setup' and 'class="active"' or ''}>
          <a href="/configure/setup">
            <i class="fa fa-fw"></i><span>Setup</span>
          </a>
        </li>
%endif
%if req.remote_user.roleid > req.remote_user.role.READONLY_ADMIN:
        <li ${obj.active=='general' and 'class="active"' or ''}>
          <a href="/configure/general">
            <i class="fa fa-fw"></i><span>General</span>
          </a>
        </li>
%endif
        <li ${obj.active=='users' and 'class="active"' or ''}>
          <a href="/configure/users">
            <i class="fa fa-fw"></i><span>Users</span>
          </a>
        </li>
        <li ${obj.active=='servers' and 'class="active"' or ''}>
          <a href="/configure/servers">
            <i class="fa fa-fw"></i><span>Machines</span>
          </a>
        </li>
        <li  ${obj.active=='yml' and 'class="active"' or ''}>
          <a href="/configure/yml">
            <i class="fa fa-fw"></i><span>Tableau Settings</span>
          </a>
        </li>
      </ul>
    </li>
%endif
  </ul>
</section>
