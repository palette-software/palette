<section class="main-side-bar">
  <section class="status">
    <span class="fa-stack">
      <i class="fa fa-circle fa-stack-1x"></i>
      <i id="status-icon" class="fa fa-fw fa-stack-1x ${obj.status_class}"></i>
    </span>
    <h1>STATUS</h1>
    <h3 id="status-text">${obj.status_text}</h3>
    <i class="fa fa-fw fa-angle-right" id="expand-right"></i>
  </section>
  <ul class="actions">
    <li ${obj.active=='home' and 'class="active"' or ''}>
      <a href="/">
        <i class="fa fa-fw fa-copy"></i><span>Events</span>
      </a>
    </li>
    <li class="${obj.active=='activity' and 'active' or ''}">
      <a href="/activity">
        <i class="fa fa-fw fa-book"></i><span>Workbook Archive</span>
      </a>
    </li>
%if req.remote_user.roleid > req.remote_user.role.NO_ADMIN:
    <li class="has-side-bar ${obj.active=='manage' and 'active' or ''}">
      <a href="/manage">
        <i class="fa fa-fw fa-wrench"></i><span>Manage Tableau</span>
      </a>
    </li>
%if req.remote_user.roleid > req.remote_user.role.READONLY_ADMIN:
    <li class="category">
      <a>
        <i class="fa fa-fw fa-gears"></i><span>Integration</span>
        <i class="fa fa-fw fa-angle-${obj.integration and 'up' or 'down'} expand"></i>
      </a>
      <ul ${obj.integration and 'class="visible"' or ''}>
        <li ${obj.active=='s3' and 'class="active"' or ''}>
          <a href="/configure/s3">
            <i class="fa fa-fw fa-cubes"></i><span>AWS S3</span>
          </a>
        </li>
        <li ${obj.active=='gcs' and 'class="active"' or ''}>
          <a href="/configure/gcs">
            <i class="fa fa-fw fa-google"></i><span>Google Storage</span>
          </a>
        </li>
      </ul>
    </li>
%endif
    <li class="category">
      <a>
        <i class="fa fa-fw fa-cog"></i><span>Configuration</span>
        <i class="fa fa-fw fa-angle-${obj.expanded and 'up' or 'down'} expand"></i>
      </a>
      <ul ${obj.expanded and 'class="visible"' or ''}>
%if req.remote_user.roleid > req.remote_user.role.READONLY_ADMIN:
        <li ${obj.active=='general' and 'class="active"' or ''}>
          <a href="/configure/general">
            <i class="fa fa-fw fa-edit"></i><span>General</span>
          </a>
        </li>
%endif
        <li ${obj.active=='users' and 'class="active"' or ''}>
          <a href="/configure/users">
            <i class="fa fa-fw fa-group"></i><span>Users</span>
          </a>
        </li>
        <li ${obj.active=='servers' and 'class="active"' or ''}>
          <a href="/configure/servers">
            <i class="fa fa-fw fa-laptop"></i><span>Machines</span>
          </a>
        </li>
        <li  ${obj.active=='yml' and 'class="active"' or ''}>
          <a href="/configure/yml">
            <i class="fa fa-fw tableau"></i><span>Tableau Settings</span>
          </a>
        </li>
      </ul>
    </li>
%endif
  </ul>
</section>
