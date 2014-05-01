<script src="/app/module/palette/js/vendor/jquery.js"></script>
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
