# -*- coding: utf-8 -*- 
<%inherit file="layout.mako" />

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

<script type="text/javascript">
	$(function(){
		$('#toggle-side-menu').bind('click', function() {
			$('.main-side-bar').toggleClass('collapsed');
		});

		$('#mainNav .container > i').bind('click', function() {
			$('.main-side-bar').toggleClass('open');
			$(this).toggleClass('open');
		});
		
	});
</script>
