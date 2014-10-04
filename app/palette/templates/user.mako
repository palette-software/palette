# -*- coding: utf-8 -*-
<%inherit file="layout.mako" />

<%block name="title">
<title>Palette - User Configuration</title>
</%block>

<section class="dynamic-content configuration">
  <h1 class="page-title">Users</h1>
  <div class="refresh">
%if req.remote_user.roleid >= req.remote_user.role.MANAGER_ADMIN:
    <i class="fa fa-fw fa-refresh inactive"></i>
%endif
    <p>
      <span class="message"></span>
      Updated <span id="last-update"></span>
    </p>
  </div>
  <div class="letters"></div>
  <div id="user-list"></div>
</section>

<script id="user-list-template" type="x-tmpl-mustache">
  {{#users}}
  <article class="item">
    <div class="summary clearfix">
      <i class="fa fa-fw fa-user"></i>
      <div>
        <div class="col2">
          <h3>{{friendly-name}}</h3>
          <p>{{visited-info}}</p>
        </div>
        <div class="col2">
          <div>
            <span class="label">Palette Role</span>
            <span class="display-role">{{palette-display-role}}</span>
          </div>
          <div class="email-level">
            <span class="label">Email Alerts</span>
            <div class="onoffswitch"
                 data-name="{{name}}" data-href="/rest/users/email-level">
              {{email-level}}
            </div>
          </div>
        </div>
      </div>
      <i class="fa fa-fw fa-angle-down expand"></i>
    </div>
    <div class="description clearfix">
      <div>
        <div class="col2">
          <p class="heading">Tableau User Details</span>
          <article>
            <span class="label">User Name</span>{{name}}
          </article>
          <article>
            <span class="label">License Level</span>{{license-info}}
          </article>
          <article>
            <span class="label">Role</span>{{tableau-info}}
          </article>

          <article><span class="label">Email</span>
%if req.remote_user.roleid >= req.remote_user.role.MANAGER_ADMIN:
            <span class="editbox email" 
                  data-name="{{name}}" data-href="/rest/users/email">
              {{email}}
            </span>
%else:
	    <span>{{email}}</span>
%endif
          </article>
          <article>
            <span class="label">Created</span>{{system-created-at}}
          </article>
          <article>
            <span class="label">Last Tableau Login</span>{{login-at}}
          </article>
        </div>
        <div class="col2">
%if req.remote_user.roleid == req.remote_user.role.SUPER_ADMIN:
          <article>
            <span class="label">Palette Admin Permissions</span>
            <i class="fa fa-fw fa-question-circle fa-2x help"></i>
          </article>
          <div class="btn-group dropdown">
            <button type="button" class="btn btn-default dropdown-toggle"
                    data-toggle="dropdown">
              <div>{{admin-type}}</div><span class="caret"></span>
            </button>
            <ul class="dropdown-menu" role="menu">
                  {{#admin-levels}}
              <li><a data-userid="{{userid}}" data-roleid="{{id}}"
                     href="/rest/users/admin">{{name}}</a></li>
                  {{/admin-levels}}
            </ul>
          </div>
%endif
        </div>
      </div>
    </div>
  </article>
  {{/users}}
</script>

<script src="/app/module/palette/js/vendor/require.js" data-main="/app/module/palette/js/users.js">
</script>
