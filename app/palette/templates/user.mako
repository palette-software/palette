# -*- coding: utf-8 -*-
<%inherit file="layout.mako" />

<%block name="title">
<title>Palette - User Configuration</title>
</%block>

<section class="config-content">
  <section class="top-zone">
    <h1 class="page-title">Users</h1>
  </section>
  <section class="bottom-zone">
    <div id="user-list"></div>
  </section>
</section>

<script id="user-list-template" type="x-tmpl-mustache">
  {{#users}}
  <article class="event">
    <i class="fa fa-fw fa-user"></i>
    <h3>{{friendly-name}}</h3>
    <p>Last Visited Jan 1, 1970 at 12:00AM PT</p>
    <div>
      <div class="col-md-4">
        <article><span class="label">Tableau User Name</span>{{name}}</article>
        <article>
          <span class="label">License Level</span>{{license-level}}
        </article>
        <article><span class="label">Email</span>
          <span class="editbox" data-href="">{{email}}</span>
        </article>
        <article><span class="label">Created</span>{{created}}</article>
        <article><span class="label">Updated</span>{{updated}}</article>
      </div>
      <div class="col-md-4">
        <article>
          <span class="label">Palette Admin Permissions</span>
          <i class="fa fa-fw fa-question-circle fa-2x help"></i>
        </article>
        <div class="btn-group dropdown">
          <button type="button" class="btn btn-default dropdown-toggle"
                  data-toggle="dropdown">
            <div>No Admin</div><span class="caret"></span>
          </button>
          <ul class="dropdown-menu" role="menu">
            <li><a href="#">No Admin</a></li>
            <li><a href="#">Read-Only Admin</a></li>
            <li><a href="#">Manager Admin</a></li>
            <li><a href="#">Super Admin</a></li>
          </ul>
        </div>
      </div>
    </div>
  </article>
  {{/users}}
</script>

<script src="/app/module/palette/js/vendor/require.js" data-main="/app/module/palette/js/users.js">
</script>
