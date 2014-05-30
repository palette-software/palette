# -*- coding: utf-8 -*-
<%inherit file="configure.mako" />

<%block name="title">
<title>Palette - Billing</title>
</%block>

<section class="dynamic-content">
  <h1 class="page-title">Billing</h1>
  <section class="row bottom-zone">
    <div class="col-sm-12 col-md-8 col-lg-6">
      <label>Card Info</label>
      <input type="text" name="cardnumber" placeholder="Credit Card Number" />
      <input type="text" name="cardname" placeholder="Name on Card" />
      <div class="btn-group">
        <button type="button" class="btn btn-default dropdown-toggle" data-toggle="dropdown"><div>Card Type</div><span class="caret"></span>
        </button>
        <ul class="dropdown-menu" role="menu">
          <li><a href="#">Card Type</a></li>
          <li><a href="#">Card Type</a></li>
        </ul>
      </div>
      <section class="row">
        <section class="col-xs-6">
          <input type="text" name="expdate" placeholder="Exp. Date (mm/dd/yyyy)" />
        </section>
        <section class="col-xs-6">
          <input type="text" name="cvc" placeholder="CVC" />
        </section>
      </section>
      <label>Billing Address</label>
      <input type="text" name="address" placeholder="Address" />
      <section class="row">
        <section class="col-xs-12 col-md-6">
          <input type="text" name="state" placeholder="State" />
          <input type="text" name="zip" placeholder="Zip Code" />
        </section>
        <secton class="col-xs-12 col-md-6">
          <input type="text" name="city" placeholder="City" />
          <div class="btn-group">
            <button type="button" class="btn btn-default dropdown-toggle" data-toggle="dropdown"><div>Country</div><span class="caret"></span>
            </button>
            <ul class="dropdown-menu" role="menu">
              <li><a href="#">Country</a></li>
              <li><a href="#">Country</a></li>
              <li><a href="#">Country</a></li>
            </ul>
          </div>
      </section>
      <label>Contact Info</label>
      <input type="text" name="fullname" placeholder="Full Name" />
      <input type="text" name="phonenumber" placeholder="Phone Number (123-123-1234)" />
      <input type="email" name="email" placeholder="Email" />
      <section class="row margin-top">
        <section class="col-xs-12 col-sm-6">
          <button type="submit" name="save" class="p-btn">Save</button>
        </section>
        <section class="col-xs-12 col-sm-6">
          <!-- ONLY SHOW AFTER SAVE IS PRESSED <button type="submit" name="revert" class="p-btn"><span class="fi-refresh"></span> Revert</button></section>-->
        </section>
      </section>
    </div>
  </section>
</section>

<script src="/app/module/palette/js/vendor/require.js" data-main="/app/module/palette/js/billing.js">
</script>
