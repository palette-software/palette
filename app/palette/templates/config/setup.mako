# -*- coding: utf-8 -*-
<%inherit file="../webapp.mako" />

<%block name="title">
<title>Palette - Setup Configuration</title>
</%block>

<div class="content setup-page">
  <div>
    <div class="top-zone">
      <h1>Setup Configuration</h1>
    </div> <!-- top-zone -->
    <div class="bottom-zone">
%if req.platform.product != req.platform.PRODUCT_PRO:
      <a name="url"></a>
      <section class="form-group">
        <%include file="server-url.mako" />
        <div class="save-cancel">
          <button type="button" id="cancel-url" class="cancel disabled">
            Cancel
          </button>
          <button type="button" id="save-url" class="save disabled">
            Save
          </button>
        </div>
      </section>
%endif

      <a name="tableau-server-url"></a>
%if req.platform.product != req.platform.PRODUCT_PRO:
      <hr />
%endif
      <section class="form-group">
        <%include file="tableau-server-url.mako" />
        <div class="save-cancel">
          <button type="button" id="cancel-tableau-url" class="cancel disabled">
            Cancel
          </button>
          <button type="button" id="save-tableau-url" class="save disabled">
            Save
          </button>
        </div>
      </section>

      <a name="admin"></a>
      <hr />
      <section  class="form-group" id="admin">
        <a id="236536" data-toggle="help" href="#"><i class="help"></i></a>
        <h2>Palette Server Admin Credentials</h2>
        <p>Change the password for the built-in "Palette" username.</p>
        <p>Any combination of 8+ case-sensitive, alphanumeric characters (i.e. A-Z, a-z, 0-9, and !,@,#,$,%).</p>
        <label>Username</label>
        <p class="fake-text-input">Palette</p>
        <label class="control-label required" for="password">New Password</label>
        <input type="password" class="form-control" id="password" />
        <label class="control-label" for="confirm-password">Confirm New Password</label>
        <input type="password" class="form-control" id="confirm-password" />
        <div class="save-cancel">
          <button type="button" id="cancel-admin" class="cancel disabled">
            Cancel
          </button>
          <button type="button" id="save-admin" class="save disabled">
            Save
          </button>
        </div>
      </section>

%if req.platform.product != req.platform.PRODUCT_PRO:
      <a name="mail"></a>
      <hr />
      <section class="form-group" id="mail">
        <%include file="mail.mako" />
        <div class="save-cancel">
          <button type="button" id="cancel-mail" class="cancel disabled">
            Cancel
          </button>
          <button type="button" id="save-mail" class="save disabled">
            Save
          </button>
        </div>
      </section>

      <a name="ssl"></a>
      <hr />
      <section class="form-group" id="ssl">
        <%include file="ssl.mako" />
        <div class="save-cancel">
          <button type="button" id="cancel-ssl" class="cancel disabled">
            Cancel
          </button>
          <button type="button" id="save-ssl" class="save disabled">
            Save
          </button>
        </div>
      </section>
%endif

      <a name="tz"></a>
      <hr />
      <section class="form-group" id="tz">
        <%include file="tz.mako" />
        <div class="save-cancel">
          <button type="button" id="cancel-tz" class="cancel disabled">
            Cancel
          </button>
          <button type="button" id="save-tz" class="save disabled">
            Save
          </button>
        </div>
      </section>

      <a name="auth"></a>
      <hr />
      <section class="form-group" id="auth">
        <a id="236544" data-toggle="help" href="#"><i class="help"></i></a>
        <h2>Authentication</h2>
        <p>This setting overrides Palette's default Authentication Method.</p>
        <span id="authentication-type" class="btn-group"></span>
        <div class="save-cancel">
          <button type="button" id="cancel-auth" class="cancel disabled">
            Cancel
          </button>
          <button type="button" id="save-auth" class="save disabled">
            Save
          </button>
        </div>
      </section>
    </div> <!-- bottom-zone -->
  </div>
</div> <!-- content -->

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
