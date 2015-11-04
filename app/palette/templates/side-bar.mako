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
    <li class="category ${obj.archive and 'open' or ''}">
      <a data-toggle="category">
        <i class="fa fa-fw fa-copy"></i><span>Archive</span>
        <i class="expand"></i>
      </a>
      <ul>
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
    <li class="${obj.active=='support-case' and 'active' or ''}">
      <a href="/support-case">
        <i class="fa fa-fw fa-support"></i><span>Tableau Support</span>
      </a>
    </li>
%endif
  </ul>
</section>
