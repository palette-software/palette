<!DOCTYPE html>
<html>
<head>

<%block name="title">
<title>Palette</title>
</%block>

<%block name="favicon">
<%include file="favicon.mako" />
</%block>

<%block name="fullstyle">
<meta charset="utf-8">
<meta name="viewport" content="width=1000,minimal-ui">
<meta name="apple-mobile-web-app-capable" content="yes">
<link rel="stylesheet" type="text/css" href="/app/module/palette/css/bootstrap.min.css">
<link rel="stylesheet" type="text/css" href="/app/module/palette/css/font-awesome.min.css">
<link rel="stylesheet" type="text/css" href="/app/module/palette/fonts/fonts.css">
<link rel="stylesheet" type="text/css" href="/app/module/palette/css/style.css" media="screen">
</%block>

<script>
  var require = {
    paths: {
      'jquery': '/app/module/palette/js/vendor/jquery',
      'underscore': '/app/module/palette/js/vendor/underscore',
      'topic': '/app/module/palette/js/vendor/pubsub',
      'template' : '/app/module/palette/js/vendor/mustache',
      'domReady': '/app/module/palette/js/vendor/domReady',

      'bootstrap': '/app/module/palette/js/vendor/bootstrap',
      'lightbox': 'http://www.helpdocsonline.com/v2/lightbox'
    },
    shim: {
      'bootstrap': {
         deps: ['jquery']
      },
      'lightbox': {
         deps: ['jquery']
      }

    }
  };
</script>

<script id="server-list-template" type="x-tmpl-mustache">
  {{#environments}}
  <h1>{{name}}</h1>
  <ul class="server-list">
    {{#agents}}
    <li>
      <a>
        <i class="fa fa-fw fa-laptop {{color}}"></i>
            <div>
          <h5>{{displayname}}</h5>
          <span class="hostname">{{hostname}}</span>
          <span class="address">{{ip_address}}</span>
            </div>
        <i class="fa fa-fw fa-angle-down down-arrow"></i>
      </a>
      <ul class="processes {{visible}}">
        {{#volumes}}
        <li>
          <i class="fa fa-fw fa-circle {{color}}"></i>
          Storage: {{name}} {{value}}
        </li>
        {{/volumes}}
        {{#cpu}}
        <li>
          <i class="fa fa-fw fa-circle {{color}}"></i>
          CPU
        </li>
        {{/cpu}}
        {{#license}}
        <li>
          <i class="fa fa-fw fa-circle {{color}}"></i>
          License: Tableau
        </li>
        {{/license}}
        {{#in_ports}}
        <li>
           <i class="fa fa-fw fa-circle {{color}}"></i>
           NETin: {{name}} ({{num}})
        </li>
        {{/in_ports}}
        {{#out_ports}}
        <li>
           <i class="fa fa-fw fa-circle {{color}}"></i>
           NETout: {{name}} ({{num}})
        </li>
        {{/out_ports}}
        {{#details}}
        <li>
          <i class="fa fa-fw fa-circle {{color}}"></i>
          {{name}} ({{pid}})
        </li>
        {{/details}}
        {{#warnings}}
        <li>
          <i class="fa fa-fw fa-circle {{color}}"></i>
          {{message}}
        </li>
        {{/warnings}}
      </ul>
    </li>
    {{/agents}}
  </ul>
  {{/environments}}
</script>

<script id="editbox-view" type="x-tmpl-mustache">
  <span>{{value}}</span>
  <i class="fa fa-fw fa-pencil"></i>
</script>

<script id="editbox-edit" type="x-tmpl-mustache">
  <input type="text" value="{{value}}" />
  <i class="fa fa-fw fa-check ok"></i>
  <i class="fa fa-fw fa-times cancel"></i>
</script>

<!-- FIXME: duplicated? -->
<script id="filter-dropdown" type="x-tmpl-mustache">
  <button type="button" class="btn btn-default dropdown-toggle" data-toggle="dropdown"><div data-id="{{id}}">{{value}}</div><span class="caret"></span>
  </button>
  <ul class="dropdown-menu" role="menu">
    {{#options}}
    <li><a data-id="{{id}}">{{option}}</a></li>
    {{/options}}
  </ul>
</script>


</head>
<body>

<%include file="_nav.mako" />

<div class="wrapper">
<div class="container">

<%include file="side-bar.mako" />

<section class="secondary-side-bar servers">
  <div id="server-list"></div>
</section>

${next.body()}
</div>
</div>

<article class="popup" id="okcancel">
  <section class="popup-body">
    <section class="row">
      <section class="col-xs-12">
        <p>&nbsp;</p>
      </section>
    </section>
    <section class="row">
      <section class="col-xs-6">
        <button class="p-btn popup-ok">OK</button>
      </section>
      <section class="col-xs-6">
        <button class="p-btn popup-close">Cancel</button>
      </section>
    </section>
  </section>
  <div class="shade">&nbsp;</div>
</article>

<%include file="dropdown.mako" />
<%include file="onoff.mako" />

</body>
</html>
