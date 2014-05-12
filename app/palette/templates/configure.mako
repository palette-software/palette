# -*- coding: utf-8 -*- 
<%inherit file="layout.mako" />

<section class="secondary-side-bar config">
  <ul class="actions">
    <li class="divider">&nbsp;</li>
    <li ${obj.configure_active == 'profile' and 'class="active"' or ''}>
      <a href="/configure/profile">
        <i class="fa fa-fw fa-user"></i>
        <span>Profile</span>
      </a>
    </li>
    <li ${obj.configure_active == 'billing' and 'class="active"' or ''}>
      <a href="/configure/billing">
        <i class="fa fa-fw fa-credit-card"></i>
        <span>Billing</span>
      </a>
    </li>
    <li ${obj.configure_active == 'yml' and 'class="active"' or ''}>
      <a href="/configure/yml">
        <i class="fa fa-fw fa-cog"></i>
        <span>Tableau Settings</span>
      </a>
    </li>
    <li ${obj.configure_active == 'splunk' and 'class="active"' or ''}>
      <a href="/configure/splunk">
        <i class="fa fa-fw fa-arrows-alt"></i>
        <span>Splunk Integration</span>
      </a>
    </li>
  </ul>
</section>

${next.body()}
