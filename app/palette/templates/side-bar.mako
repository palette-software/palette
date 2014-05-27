<section class="main-side-bar">
  <section class="status">
    <img id="status-image" src="/app/module/palette/images/blank.png">
    <h2>Status</h2>
    <h3 id="status-text"></h3>
  </section>
  <ul class="actions">
    <li class="divider">&nbsp;</li>
    <li ${obj.main_active=='home' and 'class="active"' or ''}>
      <a href="/"><i class="fa fa-fw fa-home"></i><span>Home</span>
	  </a>
    </li>
    <li ${obj.main_active=='extracts' and 'class="active"' or ''}>
      <a href="/extracts"><i class="fa fa-fw fa-copy"></i>
	    <span>Extracts</span>
	  </a>
    </li>
    <li ${obj.main_active=='manage' and 'class="active"' or ''}>
      <a href="/manage"><i class="fa fa-fw fa-wrench"></i>
	    <span>Manage Tableau</span>
	  </a>
    </li>
    <li class="divider">&nbsp;</li>
    <li class="Phidden-tiny" ${obj.main_active=='configure' and 'class="active"' or ''}>
      <a href="/configure/yml">
        <i class="fa fa-fw fa-cog"></i>
        <span>Configure</span>
      </a>
    </li>
  </ul>
  <i id="toggle-side-menu" class="fa fa-fw fa-arrow-left"></i>
</section>
