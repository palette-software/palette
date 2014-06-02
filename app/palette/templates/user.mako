# -*- coding: utf-8 -*-
<%inherit file="layout.mako" />

<%block name="title">
<title>Palette - User Configuration</title>
</%block>

<section class="dynamic-content">
  <h1 class="page-title">Users</h1>
  <div id="user-list"></div>
</section>

<script id="user-list-template" type="x-tmpl-mustache">
  {{#users}}
  <article class="event">
    <div class="summary clearfix">
      <i class="fa fa-fw fa-user"></i>
      <div>
	<div class="col2">
	  <h3>{{friendly-name}}</h3>
	  <p>Last Visited Jan 1, 1970 at 12:00AM PT</p>
	</div>
	<div class="col2">
	  <p>{{friendly-name}}</p>
	  <p>Last Visited Jan 1, 1970 at 12:00AM PT</p>
	</div>
      </div>
      <i class="fa fa-fw fa-angle-down expand"></i>
    </div>
    <div class="description clearfix">
      <div>
	    <div class="col2">
          <article>
	        <span class="label">Tableau User Name</span>{{name}}</article>
          <article>
            <span class="label">License Level</span>{{license-level}}
          </article>
          <article><span class="label">Email</span>
            <span class="editbox" data-href="">{{email}}</span>
          </article>
          <article><span class="label">Created</span>{{created}}</article>
          <article><span class="label">Updated</span>{{updated}}</article>
	    </div>
	    <div class="col2">
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
	    </div>
      </div>
    </div>
  </article>
  {{/users}}
</script>

<script src="/app/module/palette/js/vendor/require.js" data-main="/app/module/palette/js/users.js">
</script>
