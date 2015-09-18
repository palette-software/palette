# -*- coding: utf-8 -*-
<%inherit file="../layout.mako" />

<%block name="title">
<title>Palette - Setup Configuration</title>
</%block>

<div class="dynamic-content configuration setup-page">
  <div class="scrollable">

    <a name="url"></a>
    <section class="top-zone">
      <section class="row">
        <section class="col-xs-12">
          <h1>Setup Configuration</h1>
        </section>
      </section>
    </section>

%if req.platform.product != req.platform.PRODUCT_PRO:
    <section>
      <%include file="server-url.mako" />
      <div class="save-cancel">
        <button type="button" id="save-url" class="btn btn-primary disabled">
          Save
        </button>
        <button type="button" id="cancel-url" class="btn btn-primary disabled">
          Cancel
        </button>
      </div>
    </section>
%endif

    <a name="tableau-server-url"></a>
%if req.platform.product != req.platform.PRODUCT_PRO:
    <hr />
%endif
    <section>
      <%include file="tableau-server-url.mako" />
      <div class="save-cancel">
        <button type="button" id="save-tableau-url" class="btn btn-primary disabled">
          Save
        </button>
        <button type="button" id="cancel-tableau-url" class="btn btn-primary disabled">
          Cancel
        </button>
      </div>
    </section>

    <a name="admin"></a>
    <hr />
    <section id="admin">
      <a id="236536" href="#"><i class="fa fa-question-circle help"></i></a>
      <h2>Palette Server Admin Credentials</h2>
      <p>Change the password for the built-in "Palette" username.</p>
      <p>Any combination of 8+ case-sensitive, alphanumeric characters (i.e. A-Z, a-z, 0-9, and !,@,#,$,%).</p>
      <label>Username</label>
      <p class="fake-text-input">Palette</p>
      <label for="password">New Password *</label>
      <input type="password" id="password" />
      <label for="confirm-password">Confirm New Password *</label>
      <input type="password" id="confirm-password" />
      <div class="save-cancel">
        <button type="button" id="save-admin" class="btn btn-primary disabled">
          Save
        </button>
        <button type="button" id="cancel-admin" class="btn btn-primary disabled">
          Cancel
        </button>
      </div>
    </section>

%if req.platform.product != req.platform.PRODUCT_PRO:
    <a name="mail"></a>
    <hr />
    <section id="mail">
      <%include file="mail.mako" />
      <div class="save-cancel">
        <button type="button" id="save-mail" class="btn btn-primary disabled">
          Save
        </button>
        <button type="button" id="cancel-mail" class="btn btn-primary disabled">
          Cancel
        </button>
      </div>
    </section>

    <a name="ssl"></a>
    <hr />
    <section id="ssl">
      <%include file="ssl.mako" />
      <div class="save-cancel">
        <button type="button" id="save-ssl" class="btn btn-primary disabled">
          Save
        </button>
        <button type="button" id="cancel-ssl" class="btn btn-primary disabled">
          Cancel
        </button>
      </div>
    </section>
%endif

    <a name="tz"></a>
    <hr />
    <section id="tz">
      <%include file="tz.mako" />
      <div class="save-cancel">
        <button type="button" id="save-tz" class="btn btn-primary">
          Save
        </button>
        <button type="button" id="cancel-tz" class="btn btn-primary">
          Cancel
        </button>
      </div>
    </section>

    <a name="auth"></a>
    <hr />
    <section id="auth">
      <a id="236544" href="#"><i class="fa fa-question-circle help"></i></a>
      <h2>Authentication</h2>
      <p>This setting overrides Palette's default Authentication Method.</p>
      <span id="authentication-type" class="btn-group"></span>
      <div class="save-cancel">
        <button type="button" id="save-auth" class="btn btn-primary">
          Save
        </button>
        <button type="button" id="cancel-auth" class="btn btn-primary">
          Cancel
        </button>
      </div>
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

<script src="/js/vendor/require.js" data-main="/js/setup.js">
</script>
