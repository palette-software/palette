<section class="main-side-bar">
  <section class="status">
    <img id="status-image" src="/app/module/palette/images/blank.png">
    <h2>Status</h2>
    <h3 id="status-text"></h3>
  </section>
  <ul class="actions">
    <li ${obj.active=='home' and 'class="active"' or ''}>
      <a href="/"><i class="fa fa-fw fa-home"></i><span>Home</span>
	  </a>
    </li>
    <li ${obj.active=='extracts' and 'class="active"' or ''}>
      <a href="/extracts"><i class="fa fa-fw fa-copy"></i>
	    <span>Extracts</span>
	  </a>
    </li>
    <li ${obj.active=='manage' and 'class="active"' or ''}>
      <a href="/manage"><i class="fa fa-fw fa-wrench"></i>
	    <span>Manage Tableau</span>
	  </a>
    </li>
    <li class="category Phidden-tiny">
      <a href="/configure/yml">
        <i class="fa fa-fw fa-cog"></i>
        <span>Configure</span>
	<i class="fa fa-fw fa-angle-${obj.expanded and 'up' or 'down'} expand"></i>
      </a>
      <ul ${obj.expanded and 'class="visible"' or ''}>
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
	<li  ${obj.active=='yml' and 'class="active"' or ''}>
	      <a href="/configure/yml">
            <i class="fa fa-fw tableau"></i>
            <span>Tableau Settings</span>
	      </a>
	    </li>
      </ul>
    </li>
  </ul>
  <i id="toggle-side-menu" class="fa fa-fw fa-arrow-left"></i>
</section>
