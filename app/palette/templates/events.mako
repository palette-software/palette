# -*- coding: utf-8 -*-
<div class="scrollable">
  <div class="top-zone">
    <%include file="paging.mako" args="name='Events'" />
    <h1>Events</h1>
    <section class="row">
      <section class="col-xs-12 filter-dropdowns">
        <div id="status-dropdown" class="btn-group"></div>
        <div id="type-dropdown" class="btn-group"></div>
      </section>
    </section>
  </section>
  <section class="bottom-zone">
    <section id="event-list"></section>
    <%include file="paging.mako" args="name='Events'" />
  </section>

  <script id="event-list-template" type="x-tmpl-mustache">
    {{#events}}
    <article class="item" id="item{{eventid}}">
      <div class="summary clearfix">
        <span class="fa-stack">
          <i class="fa fa-circle fa-stack-1x"></i>
          <i class="fa fa-fw fa-stack-1x {{icon}} {{color}}"></i>
        </span>
        <div>
          <h3>{{title}}</h3>
          <p>{{summary}}</p>
        </div>
        <i class="fa fa-fw fa-angle-down expand"></i>
      </div>
      <div class="description">{{{description}}}</div>
    </article>
    {{/events}}
  </script>
</div>
