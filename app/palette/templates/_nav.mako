<nav id="mainNav" data-topbar>
	<div class="container">
		<%include file="_logo.mako" />
		<span id="toggle-main-menu" class="fi-list"></span>
		<ul id="nav">
			<li id="home" class="active-home"><a href="/"><span class="fi-home"></span> Home</a></li>
			<li id="settings" class="active-profile">
				<a href="/profile"><span class="fi-widget"></span> Settings</a>
			</li>
			<li id="help" class="more active-help">
				<a href="#"><span class="fi-plus"></span> Help<span class="arrow-down"></span></a></span>
				<ul>
					<li><a href="/support/ticket"><span class="fi-ticket"></span> Create Support Ticket</a></li></li>
					<li><a href="/support/contact"><span class="fi-megaphone"></span> Contact Support</a></li>
				</ul>
			</li>
			<li id="logout"><a href="/logout"><span class="fi-power"></span> Logout</a></li>
		</ul>
	</div>
</nav>
