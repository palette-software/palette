# -*- coding: utf-8 -*- 
<%inherit file="layout.mako" />

<section class="secondary-side-bar config">
  <ul class="actions">
    <li class="divider">&nbsp;</li>
    <li ${obj.configure_active == 'yml' and 'class="active"' or ''}>
      <a href="/configure/yml">
        <i class="fa fa-fw fa-cog"></i>
        <span>Tableau Settings</span>
      </a>
    </li>
  </ul>
</section>

${next.body()}
