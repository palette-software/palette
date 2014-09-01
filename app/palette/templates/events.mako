<section class="top-zone">
  <section class="row">
    <section class="col-xs-12">
      <h1 class="page-title">Events</h1>
    </section>
  </section>
  <section class="row">
    <section class="col-xs-12 event-dropdowns">
      <div id="event-count"><span>0</span> Events</div>
      <div id="status-dropdown" class="btn-group"></div>
      <div id="type-dropdown" class="btn-group"></div>
    <div class="event-pagination">
      <div>
	Page <span class="page-number"></span> of <span class="page-count"> </span>
      </div>
      <span class="first"><a href="#">first</a> |</span>
      <span class="previous"><a href="#">previous</a> |</span>
      <span class="next"><a href="#">next</a> |</span>
      <span class="last"><a href="#">last</a></span>
    </div>
    </section>
  </section>
</section>
<section class="bottom-zone">
  <section id="event-list"></section>
  <section class="event-pagination">
    <div>
    Page <span class="page-number"></span> of <span class="page-count"> </span>
    </div>
    <span class="first"><a href="#">first</a> |</span>
    <span class="previous"><a href="#">previous</a> |</span>
    <span class="next"><a href="#">next</a> |</span>
    <span class="last"><a href="#">last</a></span>
  </section>
</section>

<script id="event-list-template" type="x-tmpl-mustache">
  {{#events}}
  <article class="event">
    <div class="summary clearfix">
      <i class="fa fa-fw {{icon}} {{color}}"></i>
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

<script id="event-dropdown-template" type="x-tmpl-mustache">
  <button type="button" class="btn btn-default dropdown-toggle" data-toggle="dropdown"><div data-id="{{id}}">{{value}}</div><span class="caret"></span>
  </button>
  <ul class="dropdown-menu" role="menu">
    {{#options}}
    <li><a data-id="{{id}}">{{item}}</a></li>
    {{/options}}
  </ul>
</script>
