# -*- coding: utf-8 -*- 
<%inherit file="_layout.mako" />

<%block name="title">
<title>Palette - Activities </title>
</%block>

<%block name="favicon">
<%include file="favicon.mako" />
</%block>
<%block name="fullstyle">
<meta charset="utf-8">
<meta name="viewport" content="initial-scale=1, maximum-scale=1, user-scalable=no, width=device-width">
<link href='http://fonts.googleapis.com/css?family=Roboto:300,500' rel='stylesheet' type='text/css'>
<link rel="stylesheet" type="text/css" href="/app/module/palette/css/normalize.css" media="screen">
<link rel="stylesheet" type="text/css" href="/app/module/palette/css/bootstrap.min.css">
<link rel="stylesheet" type="text/css" href="/app/module/palette/css/font-awesome.min.css">
<link rel="stylesheet" type="text/css" href="/app/module/palette/css/style.css" media="screen">

<script src="/app/module/palette/js/vendor/modernizr.js"></script>

<style type="text/css">
  .main-side-bar ul.actions li.active-activity i {
    color: #53c3f1;
  }
  .main-side-bar ul.actions li.active-activity a {
    text-indent: 8px;
  }
</style>

</%block>
<%include file="side-bar.mako" />
<section class="dynamic-content">
  <section class="top-zone">
      <h1 class="page-title">Activities</h1>
      <section>
        <label class="select">
          <select class="styled-select">
            <option>Type</option>
            <option>Alerts</option>
            <option>Errors</option>
          </select>
        </label>
        <label class="select">
            <select class="styled-select">
              <option>Most Recent</option>
              <option>By Importance</option>
            </select>
        </label>
      </section>
  </section>
  <section class="row bottom-zone">
    <section class="col-lg-12">
        <article class="activity">
          <i class="fa fa-fw fa-hdd-o red"></i>
          <h3>Served Accessed</h3>
          <p>Bixly Production Server --- <span>5:03 am</span><span> 4/14/2014</span></p>
        </article>
        <article class="activity">
          <i class="fa fa-fw fa-download green"></i>
          <h3>Backup Started</h3>
          <p>Bixly Production Server --- <span>5:03 am</span><span> 4/14/2014</span></p>
        </article>
        <article class="activity">
          <i class="fa fa-fw fa-undo blue"></i>
          <h3>Restoration initializated on Xepler Production Server #2</h3>
          <p>Bixly Production Server --- <span>5:03 am</span><span> 4/14/2014</span></p>
        </article>
        <article class="activity">
          <i class="fa fa-fw fa-hdd-o"></i>
          <h3>Served Accessed</h3>
          <p>Bixly Production Server --- <span>5:03 am</span><span> 4/14/2014</span></p>
        </article>
        <article class="activity">
          <i class="fa fa-fw fa-hdd-o"></i>
          <h3>Served Accessed</h3>
          <p>Bixly Production Server --- <span>5:03 am</span><span> 4/14/2014</span></p>
        </article>
        <article class="activity">
          <i class="fa fa-fw fa-hdd-o"></i>
          <h3>Served Accessed</h3>
          <p>Bixly Production Server --- <span>5:03 am</span><span> 4/14/2014</span></p>
        </article>
        <article class="activity">
          <i class="fa fa-fw fa-hdd-o"></i>
          <h3>Served Accessed</h3>
          <p>Bixly Production Server --- <span>5:03 am</span><span> 4/14/2014</span></p>
        </article>
        <article class="activity">
          <i class="fa fa-fw fa-hdd-o red"></i>
          <h3>Served Accessed</h3>
          <p>Bixly Production Server --- <span>5:03 am</span><span> 4/14/2014</span></p>
        </article>
        <article class="activity">
          <i class="fa fa-fw fa-download green"></i>
          <h3>Backup Started</h3>
          <p>Bixly Production Server --- <span>5:03 am</span><span> 4/14/2014</span></p>
        </article>
        <article class="activity">
          <i class="fa fa-fw fa-undo blue"></i>
          <h3>Restoration initializated on Xepler Production Server #2</h3>
          <p>Bixly Production Server --- <span>5:03 am</span><span> 4/14/2014</span></p>
        </article>
        <article class="activity">
          <i class="fa fa-fw fa-hdd-o"></i>
          <h3>Served Accessed</h3>
          <p>Bixly Production Server --- <span>5:03 am</span><span> 4/14/2014</span></p>
        </article>
        <article class="activity">
          <i class="fa fa-fw fa-hdd-o"></i>
          <h3>Served Accessed</h3>
          <p>Bixly Production Server --- <span>5:03 am</span><span> 4/14/2014</span></p>
        </article>
        <article class="activity">
          <i class="fa fa-fw fa-hdd-o"></i>
          <h3>Served Accessed</h3>
          <p>Bixly Production Server --- <span>5:03 am</span><span> 4/14/2014</span></p>
        </article>
        <article class="activity">
          <i class="fa fa-fw fa-hdd-o"></i>
          <h3>Served Accessed</h3>
          <p>Bixly Production Server --- <span>5:03 am</span><span> 4/14/2014</span></p>
        </article>
    </section>
  </section>
</section>

<script>
require({
  packages: [
    { name: "palette", location: "/app/module/palette/js" }
  ]
}, [ "palette/monitor", "palette/backup", "palette/manage" ]);
</script>

<%include file="commonjs.mako" />