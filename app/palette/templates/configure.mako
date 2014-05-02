# -*- coding: utf-8 -*- 
<%inherit file="layout.mako" />

<%include file="side-bar.mako" />

<section class="secondary-side-bar">
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
  </ul>
</section>

${next.body()}
