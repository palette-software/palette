<section class="main-side-bar">
  <section class="status">
    <img id="status-image" src="/app/module/palette/images/blank.png" />
    <h2>Status</h2>
    <h3 id="status-text"></h3>
    <i class="fa fa-fw fa-angle-right" id="expand-right"></i>
  </section>
  <ul class="actions">
    <li ${obj.active=='home' and 'class="active"' or ''}>
      <a href="/">
        <i class="fa fa-fw fa-copy"></i><span>Events</span>
      </a>
    </li>
    <li class="${obj.active=='activity' and 'active' or ''}">
      <a href="/activity"><i class="fa fa-fw fa-book"></i>
        <span>Workbook Archive</span>
      </a>
    </li>
%if req.remote_user.roleid > req.remote_user.role.NO_ADMIN:
    <li class="has-side-bar ${obj.active=='manage' and 'active' or ''}">
      <a href="/manage"><i class="fa fa-fw fa-wrench"></i>
        <span>Manage Tableau</span>
      </a>
    </li>
    <li class="category">
      <a>
        <i class="fa fa-fw fa-gears"></i>
        <span>Integration</span>
        <i class="fa fa-fw fa-angle-${obj.integration and 'up' or 'down'} expand"></i>
      </a>
      <ul ${obj.integration and 'class="visible"' or ''}>
        <li ${obj.active=='s3' and 'class="active"' or ''}>
          <a href="/configure/s3">
            <i class="fa fa-fw fa-cubes"></i>
            <span>AWS S3</span>
          </a>
        </li>
        <li ${obj.active=='gcs' and 'class="active"' or ''}>
          <a href="/configure/gcs">
            <i class="fa fa-fw fa-google"></i>
            <span>Google Storage</span>
          </a>
        </li>
        <!--
        <li ${obj.active=='splunk' and 'class="active"' or ''}>
          <a href="/configure/splunk">
            <i class="fa fa-fw fa-arrows-alt"></i>
            <span>Splunk</span>
          </a>
        </li>
        -->
      </ul>
    </li>
    <li class="category">
      <a>
        <i class="fa fa-fw fa-cog"></i>
        <span>Configuration</span>
        <i class="fa fa-fw fa-angle-${obj.expanded and 'up' or 'down'} expand"></i>
      </a>
      <ul ${obj.expanded and 'class="visible"' or ''}>
        <li ${obj.active=='storage' and 'class="active"' or ''}>
          <a href="/configure/storage">
            <i class="fa fa-fw fa-edit"></i>
            <span>General</span>
          </a>
        </li>
        <li ${obj.active=='users' and 'class="active"' or ''}>
          <a href="/configure/users">
            <i class="fa fa-fw fa-group"></i>
            <span>Users</span>
          </a>
        </li>
        <li ${obj.active=='servers' and 'class="active"' or ''}>
          <a href="/configure/servers">
            <i class="fa fa-fw fa-laptop"></i>
            <span>Servers</span>
          </a>
        </li>
        <li  ${obj.active=='tabcmd' and 'class="active"' or ''}>
          <a href="/configure/tabcmd">
            <i class="fa fa-fw fa-truck"></i>
            <span>Tabcmd User</span>
          </a>
        </li>
        <li  ${obj.active=='yml' and 'class="active"' or ''}>
          <a href="/configure/yml">
            <i class="fa fa-fw tableau"></i>
            <span>Tableau Settings</span>
          </a>
        </li>
      </ul>
    </li>
%endif
  </ul>
</section>
