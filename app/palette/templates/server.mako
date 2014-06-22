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
          <p>{{fqdn}} ({{ip-address}})</p>
        </div>
        <div class="col2">
          <p>
%if req.remote_user.roleid >= req.remote_user.role.MANAGER_ADMIN:
            <span class="editbox environment" data-href="/rest/environment">
              {{environment}}
            </span>
%else:
            {{environment}}
%endif
          </p>
          <p>Connection Status {{connection-status}}</p>
        </div>
      </div>
      <i class="fa fa-fw fa-angle-down expand"></i>
    </div>
    <div class="description clearfix">
      <div>
        <div class="col2">
          <article>
	    <span class="label">Server Type</span>{{agent-type}}
	  </article>
          <br/>
          <article>
            <span class="label">Hostname</span>{{hostname}}
          </article>
          <article><span class="label">IP Address</span>{{ip-address}}</article>
          <article><span class="label">Environment</span>{{environment}}</article>
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
	    <span class="label">Select Archive Locations</span>
	  </article>
      {{#volumes}}
      <article>
        <input type="checkbox" data-id="{{volid}}" {{checkbox-state}}
           ${req.remote_user.roleid < req.remote_user.role.MANAGER_ADMIN \
                                      and 'disabled' or ''} />
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
 
