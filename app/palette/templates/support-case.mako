# -*- coding: utf-8 -*-
<%inherit file="webapp.mako" />

<%block name="title">
<title>Palette - Support Case</title>
</%block>

<div class="content support-case-page">
  <div>
    <div class="top-zone">
      <h1>Submit a case to Tableau support</h1>
    </div>
    <div class="bottom-zone">
      <section>
        <h2>Describe your problem</h2>
        <div class="form-group required">
          <label class="control-label" for="problem:statement">
            Your problem statement
          </label>
          <input type="text" id="problem:statement" 
                 class="form-control" />
        </div>
        <div class="form-group required">
          <label class="control-label" for="problem:category">
            Category
          </label>
          <span class="btn-group" id="problem:category"></span>
        </div>
        <div class="form-group required">
          <label class="control-label" for="problem:impact">
            Impact
          </label>
          <span class="btn-group" id="problem:impact"></span>
        </div>
        <div class="form-group required">
          <label class="control-label" for="problem:description">
            Description
          </label>
          <textarea rows="3" id="problem:description" class="form-control"></textarea>
        </div>
      </section>
      <hr />
      <section>
        <h2>Your contact information</h2>
        <div class="form-group required">
          <label class="control-label" for="contact:name">Name</label>
          <input type="text" id="contact:name"
                 class="form-control cache" />
        </div>
        <div class="form-group required">
          <label class="control-label" for="contact:phone">Phone</label>
          <input type="text" id="contact:phone"
                 class="form-control cache phone" />
        </div>
        <div class="form-group required">
          <label class="control-label" for="contact:email">Email</label>
          <input type="text" id="contact:email"
                 class="form-control cache email" />
        </div>
        <div class="form-group">
          <label class="control-label" for="contact:company">Company</label>
          <input type="text" id="contact:company"
                 class="form-control" />
        </div>
        <div class="form-group required">
          <label class="control-label" for="contact:language">
            Preferred Language for this request
          </label>
          <span class="btn-group" id="contact:language"></span>
        </div>
        <div class="form-group required">
          <label class="control-label" for="contact:language">
            Preferred Support timezone for this request
          </label>
          <span class="btn-group" id="contact:timezone"></span>
        </div>
      </section>
      <hr />
      <section>
        <h2>Describe your environment</h2>
        <div class="form-group required">
          <label class="control-label" for="environment:product">
            Product
          </label>
          <span class="btn-group cache" id="environment:product"></span>
        </div>
        <div class="form-group required">
          <label class="control-label" for="environment:language">
            Product Language
          </label>
          <span class="btn-group" id="environment:language"></span>
        </div>
        <div class="form-group required">
          <label class="control-label" for="environment:version">
            Product Version
          </label>
          <span class="btn-group cache" id="environment:version"></span>
        </div>
        <div class="form-group">
          <label class="control-label" for="environment:build-number">
            Build Number</label>
          <input type="text" id="environment:build-number"
                 class="form-control" />
        </div>
        <div class="form-group required">
          <label class="control-label" for="environment:operating-system">
            Operating System
          </label>
          <span class="btn-group cache" id="environment:operating-system"></span>
        </div>
        <div class="form-group">
          <label class="control-label" for="environment:data-source">
            Data Source
          </label>
          <span class="btn-group" id="environment:data-source"></span>
        </div>
      </section>
      <hr />
      <div class="checkbox">
	<label for="include-logs">
	  <input type="checkbox" id="include-logs" checked />
	  Include Tableau Server log files
	</label>
      </div>
      <div class="save-cancel">
        <button type="button" id="send-support-case"
                class="action"
                data-toggle="modal-popup"
                data-text="Are you sure you want to submit this support case?">
          Send Support Case
        </button>
      </div>
    </div> <!-- bottom-zone -->
  </div>
</div> <!-- content -->

<script src="/js/vendor/require.js" data-main="/js/support-case.js">
</script>

<script id="thank-you" type="x-tmpl-mustache">
  <h3>And that's it! Your case is on its way to Tableau Support!</h3>
  <p>
    Next, you'll get an email from Palette with a copy of your new request followed by an email from Tableau with your new case number. To check the status of your case, login to Tableau's <a href="http://customer.tableausoftware.com">Customer Portal</a>.
  </p>
</script>

