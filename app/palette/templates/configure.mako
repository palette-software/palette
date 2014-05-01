# -*- coding: utf-8 -*- 
<%inherit file="layout.mako" />

<%include file="side-bar.mako" />

<section class="secondary-side-bar profile">
  <section class="header">
    <span>Configure</span>
  </section>
  <ul class="actions">
    <li class="divider">&nbsp;</li>
    <li ${obj.configure_active == 'profile' and 'class="active"' or ''}>
      <a href="/configure/profile">
        <i class="fa fa-fw fa-home"></i>
        <span>Profile</span>
      </a>
    </li>
    <li ${obj.configure_active == 'billing' and 'class="active"' or ''}>
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

<div>
  ${obj.main_active}
</div>
