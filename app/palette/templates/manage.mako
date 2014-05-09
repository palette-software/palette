# -*- coding: utf-8 -*-
<%inherit file="layout.mako" />

<%block name="title">
<title>Palette - Manage</title>
</%block>

<section class="secondary-side-bar">
  <a class="Psmall-only" id="toggle-events" href="#"><i class="fa"></i></a>
  <h5>Production Tableau Server</h5>
  <ul class="actions">
    <li>
      <a name="popupStart" class="popup-link inactive" id="start"> 
        <i class="fa fa-fw fa-play"></i>
        <span>Start Application</span>
      </a>
    </li>
    <li>
      <a name="popupStop" class="popup-link inactive" id="stop"> 
        <i class="fa fa-fw fa-stop"></i>
        <span>Stop Application</span>
      </a>
    </li>
    <li>
      <a href="#" id="restart-ok"> 
        <i class="fa fa-fw fa-repeat inactive"></i>
        <span>Restart Application</span>
      </a>
    </li>
  </ul>
</section>

<%include file="events.mako" />

<article class="popup" id="popupStart">
  <section class="popup-body">
    <section class="row">
      <section class="col-xs-12">
        <p>Are you sure want to <span class="bold">start</span> the Tableau Server Application</p>
      </section>
    </section>
    <section class="row">
      <section class="col-xs-6">
        <button class="p-btn p-btn-grey popup-close">Cancel</button>
      </section>
      <section class="col-xs-6">
        <button id="start-ok" class="p-btn p-btn-blue">Start</button>
      </section>
    </section>
  </section>
  <div class="shade">&nbsp;</div>
</article>

<article class="popup" id="popupStop">
  <section class="popup-body">
    <section class="row">
      <section class="col-xs-12">
        <p>Are you sure want to <span class="bold">stop</span> the Tableau Server Application</p>
      </section>
    </section>
    <section class="row">
      <section class="col-xs-6">
        <button class="p-btn p-btn-grey popup-close">Cancel</button>
      </section>
      <section class="col-xs-6">
        <button id="stop-ok" class="p-btn p-btn-blue">Stop</button>
      </section>
    </section>
  </section>
  <div class="shade">&nbsp;</div>
</article>

<article class="popup" id="popupRestore">
  <section class="popup-body">
    <section class="row">
      <section class="col-xs-12">
        <p>Are you sure want to <span class="bold">restore</span> the Tableau Server Application with backup from <span class="bold"> 12:00 AM on April 15, 2014</span>?</p>
      </section>
    </section>
    <section class="row">
      <section class="col-xs-12">
        <ul class="checkbox">
          <li>
            <input type="checkbox">
              <label class="checkbox">
                <span></span>
                With configureation settings
              </label>
          </li>
          <li>
            <input type="checkbox">
              <label class="checkbox">
                <span></span>
                With backup rollback protection
              </label>
          </li>
        </ul>
      </section>
    </section>
    <section class="row">
      <section class="col-xs-6">
        <button type="submit" name="save" class="p-btn p-btn-grey popup-close">Cancel</button>
      </section>
      <section class="col-xs-6">
        <button type="submit" name="save" class="p-btn p-btn-blue">Restore</button>
      </section>
    </section>
  </section>
  <div class="shade">&nbsp;</div>
</article>

<script src="/app/module/palette/js/vendor/require.js" data-main="/app/module/palette/js/manage.js">
</script>
