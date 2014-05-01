# -*- coding: utf-8 -*- 
<%inherit file="_layout.mako" />

<%block name="favicon">
<%include file="favicon.mako" />
</%block>
<%block name="fullstyle">
<meta charset="utf-8">
<meta name="viewport" content="initial-scale=1, maximum-scale=1, user-scalable=no, width=device-width">
<link href='http://fonts.googleapis.com/css?family=Roboto:300,500' rel='stylesheet' type='text/css'>
<link rel="stylesheet" type="text/css" href="/app/module/palette/css/bootstrap.min.css">
<link rel="stylesheet" type="text/css" href="/app/module/palette/css/font-awesome.min.css">
<link rel="stylesheet" type="text/css" href="/app/module/palette/css/style.css" media="screen">
</%block>

<script src="/app/module/palette/js/vendor/modernizr.js"></script>

<style type="text/css">
.main-side-bar ul.actions li.active-profile a {
	background-color:rgba(0,0,0,0.1);
	box-shadow:0 -2px rgba(0,0,0,0.1);
}
.main-side-bar ul.actions li.active-profile a:after {
	content: "";
	position: absolute;
	right: 0;
	top: 50%;
	margin-top: -12px;
	width: 0;
	height: 0;
	border-style: solid;
	border-width: 12px 12px 12px 0;
	border-color: transparent #ececec transparent transparent;
	display: block;
}
.main-side-bar.collapsed .actions li.active-profile a {
  background-color: #ececec;
}
</style>

<%include file="side-bar.mako" />

<section class="secondary-side-bar profile">
  <section class="header">
    <span>Configure</span>
  </section>
  <ul class="actions">
    <li class="divider">&nbsp;</li>
    <li>
      <a href="/configure/profile">
        <i class="fa fa-fw fa-home"></i>
        <span>Profile</span>
      </a>
    </li>
    <li>
      <a href="/configure/billing">
        <i class="fa fa-fw fa-home"></i>
        <span>Billing</span>
      </a>
    </li>
  </ul>
</section>

${next.body()}
