# -*- coding: utf-8 -*-
<%inherit file="../layout.mako" />

<%block name="title">
<title>Palette - Setup Configuration</title>
</%block>

<div class="dynamic-content configuration setup-config-page">
  <div class="scrollable">
    <section class="top-zone">
      <section class="row">
        <section class="col-xs-12">
          <h1 class="page-title">Setup Configuration</h1>
        </section>
      </section>
    </section>
    <section>
      <%include file="mail.mako" />
    </section>
    <section>
      <button type="button" id="save-mail-settings"
              class="btn btn-primary disabled">
	    Save
      </button>
      <button type="button" id="cancel" class="btn btn-primary">
	    Cancel
      </button>
    </section>
  </div>
</div>

<script id="dropdown-template" type="x-tmpl-mustache">
  <button type="button" class="btn btn-default dropdown-toggle" data-toggle="dropdown"><div data-id="{{id}}">{{value}}</div><span class="caret"></span>
  </button>
  <ul class="dropdown-menu" role="menu">
    {{#options}}
    <li><a data-id="{{id}}">{{item}}</a></li>
    {{/options}}
  </ul>
</script>

<script src="/app/module/palette/js/vendor/require.js" data-main="/app/module/palette/js/setup.js">
</script>
