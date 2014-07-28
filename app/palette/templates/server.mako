# -*- coding: utf-8 -*-
<%inherit file="layout.mako" />

<%block name="title">
<title>Palette - Server Configuration</title>
</%block>

<section class="dynamic-content">
  <h1 class="page-title">Servers</h1>
  <div id="server-detail"></div>
</section>

<script id="server-detail-template" type="x-tmpl-mustache">
  {{#servers}}
  <article class="event">
    <div class="summary clearfix">
      <i class="fa fa-fw fa-laptop"></i>
      <div>
        <div class="col2">
          <h3>
%if req.remote_user.roleid >= req.remote_user.role.MANAGER_ADMIN:
	        <span class="editbox displayname"
		          data-id="{{agentid}}" data-href="/rest/servers/displayname">
              {{displayname}}
            </span>
%else:
            {{displayname}}
%endif
	      </h3>
          <span class=label>Hostname</span>{{fqdn}} ({{ip-address}})
        </div>
        <div class="col2">
%if req.remote_user.roleid >= req.remote_user.role.MANAGER_ADMIN:
            <div>
              <span class="label">Environment</span><span class="editbox environment" data-href="/rest/environment">
              {{environment}}
              </span>
            </div>
%else:
            <div>
              {{environment}}
            </div>
%endif
          <div class="monitor">
            <span class="label">Monitor</span>
            <div class="onoffswitch"
                 data-id="{{agentid}}" data-href="/rest/servers/monitor">
              {{enabled}}
            </div>
          </div>
        </div>
      </div>
      <i class="fa fa-fw fa-angle-down expand"></i>
    </div>
    <div class="description clearfix">
      <div>
        <div class="col2">
          <article>
	    <span class="label">Server Type</span>{{type-name}}
	  </article>
          <article><span class="label">IP Address</span>{{ip-address}}</article>
          <article><span class="label">OS</span>{{os-version}}</article>
	  <article>
	    <span class="label">RAM</span>{{installed-memory-readable}}
	  </article>
	  <article>
	    <span class="label">CPU Cores</span>{{processor-count}}
	  </article>
	  <article>
	    <span class="label">CPU Type</span>{{processor-type}}
	  </article>
	  <br/>
	</div>
	<div class="col2">
	  <article>
	    <span class="label">Attached Disks</span>
	  </article>
      {{#volumes}}
      <article>
        {{name}}: {{size-readable}} ({{available-readable}} Unused)
      </article>
      {{/volumes}}
	</div>
      </div>
    </div>
  </article>
  {{/servers}}
</script>

<script src="/app/module/palette/js/vendor/require.js" data-main="/app/module/palette/js/servers.js">
</script>
 
