# -*- coding: utf-8 -*-
<a id="236542" href="#"><i class="fa fa-question-circle help"></i></a>
<h2>Mail Server</h2>
<p>The Palette Server will send alerts using the Mail Server settings below.</p>
<div class="row">
  <div class="col-xs-6">
    <h3>Mail Server Type</h3>
    <span id="mail-server-type" class="btn-group"></span>
  </div>
  <div class="col-xs-6">
  </div>
</div>
<div class="row mail-setting">
  <div class="col-xs-6">
    <label for="alert-email-name">Palette Alert Email Name</label>
    <input type="text" id="alert-email-name" />
  </div>
  <div class="col-xs-6">
    <label for="alert-email-address">Palette Alert Email Address *</label>
    <input type="text" id="alert-email-address" />
  </div>
</div>
<div class="row mail-setting smtp">
  <div class="col-xs-6">
    <label for="smtp-server">SMTP Mail Server *</label>
    <input type="text" id="smtp-server" />
  </div>
  <div class="col-xs-6">
    <label for="smtp-port">Port *</label>
    <input type="text" id="smtp-port" />
  </div>
</div>
<div class="row mail-setting smtp">
  <div class="col-xs-6">
    <label for="smtp-username">SMTP Username</label>
    <input type="text" id="smtp-username" />
  </div>
    <div class="col-xs-6">
    <label for="smtp-password">SMTP Password</label>
    <input type="password" id="smtp-password" />
  </div>
</div>
<div class="row mail-setting">
  <div class="col-xs-10">
    <label for="test-email-recipient">Test Email Recipient</label>
    <input type="text" id="test-email-recipient" />
    <button type="button" id="test-mail" class="btn disabled">
      Test Email
    </button>
  </div>
</div>
<div class="row">
  <div class="col-xs-10">
    <p id="mail-test-message" class="hidden"></p>
  </div>
</div>
