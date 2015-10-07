# -*- coding: utf-8 -*-
<%inherit file="webapp.mako" />

<%block name="title">
<title>Palette - Support Case</title>
</%block>

<div class="dynamic-content configuration support-case-page">
  <div class="scrollable">
    <div class="top-zone">
      <h1>Submit a case to Tableau support</h1>
    </div>
    <section>
      <h2>Describe your problem</h2>
      <label for="problem-statement">Your problem statement *</label>
      <input type="text" id="problem-statement"></input>
      <label for="problem-category">Category *</label>
      <span class="btn-group" id="problem-category"></span>
      <label for="problem-impact">Impact *</label>
      <span class="btn-group" id="problem-impact"></span>
      <label for="problem-description">Description *</label>
      <textarea id="problem-description"></textarea>
    </section>
    <section>
      <h2>Your contact information</h2>
      <label for="contact-name">Name *</label>
      <input type="text" id="contact-name"></input>
      <label for="contact-phone">Phone *</label>
      <input type="text" id="contact-phone"></input>
      <label for="contact-email">Email *</label>
      <input type="text" id="contact-email"></input>
      <label for="contact-company">Company</label>
      <input type="text" id="contact-company"></input>
      <label for="contact-language">
        Preferred Language for this request *
      </label>
      <span class="btn-group" id="contact-language"></span>
      <label for="contact-language">
        Preferred Support timezone for this request *
      </label>
      <span class="btn-group" id="contact-tz"></span>
    </section>
    <div class="save-cancel">
      <button type="button" id="send-support-case"
              class="action okcancel"
              data-text="Are you sure you want to submit this support case?">
        Send Support Case
      </button>
    </div>
  </div>
</div>

<script src="/js/vendor/require.js" data-main="/js/support-case.js">
</script>
