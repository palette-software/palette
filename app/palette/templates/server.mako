# -*- coding: utf-8 -*-
<%inherit file="layout.mako" />

<%block name="title">
<title>Palette - Server Configuration</title>
</%block>

<div class="dynamic-content configuration">
  <div class="scrollable">
    <h1 class="page-title">Machines</h1>
    <div id="server-detail"></div>
  </div>
</div>

<script id="server-detail-template" type="x-tmpl-mustache">
  {{#servers}}
  <article class="item">
    <div class="summary clearfix">
      <i class="fa fa-fw fa-laptop"></i>
      <div>
        <div class="col2">
          <h3>
%if req.remote_user.roleid >= req.remote_user.role.MANAGER_ADMIN:
                <span class="editbox displayname"
                      data-id="{{agentid}}"
                      data-href="/rest/servers/displayname">
              {{displayname}}
            </span>
%else:
            {{displayname}}
%endif
          </h3>
          {{fqdn}}
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
              <span class="label">Environment</span>{{environment}}
            </div>
%endif
%if req.remote_user.roleid >= req.remote_user.role.MANAGER_ADMIN:
          <div class="monitor">
            <span class="label">Monitor</span>
            <div class="onoffswitch"
                 data-id="{{agentid}}" data-href="/rest/servers/monitor">
              {{enabled}}
            </div>
          </div>
%else:
          <div>
            <span class="label">Monitor</span>{{#enabled}}ON{{/enabled}}{{^enabled}}OFF{{/enabled}}
          </div>
%endif
        </div>
      </div>
      <i class="fa fa-fw fa-angle-down expand"></i>
    </div>
    <div class="description clearfix">
      <div>
        <div class="col2">
          <article>
            <span class="label">Server Type</span> {{type-name}}
          </article>
          {{#tableau-version}}
          <article>
            <span class="label">Tableau Server Version</span>
            {{tableau-version}} ({{tableau-bitness}}bit)
          </article>
          {{/tableau-version}}
          {{#tableau-install-dir}}
          <article>
            <span class="label">Tableau Server Directory</span>
            {{tableau-install-dir}}
          </article>
          {{/tableau-install-dir}}
          {{#tableau-license-type}}
          <article>
            <span class="label">Tableau License Type</span>
            {{tableau-license-type}}
          </article>
          {{/tableau-license-type}}
          {{#tableau-license-capacity}}
          <article>
            <span class="label">Tableau License Capacity</span>
            {{tableau-license-capacity}}
          </article>
          {{/tableau-license-capacity}}
          <article>
            <span class="label">IP Address</span> {{ip-address}}
          </article>
          <article>
            <span class="label">OS</span>
            {{os-version}}{{#bitness}} ({{bitness}}bit){{/bitness}}
          </article>
          <article>
            <span class="label">RAM</span> {{installed-memory-readable}}
          </article>
          <article>
            <span class="label">CPU Cores</span> {{processor-count}}
          </article>
          <article>
            <span class="label">CPU Type</span> {{processor-type}}
          </article>
          <br/>
        </div>
        <div class="col2">
          <article>
            <span class="label">Attached Disks</span>
          </article>
      {{#volumes}}
      <article>
        {{name}}: {{available-readable}} free of {{size-readable}}
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
