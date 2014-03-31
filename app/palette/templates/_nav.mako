<nav id="mainNav" data-topbar>
	<div class="container">
		<%include file="_logo.mako" />
		<span id="toggle-main-menu" class="fi-list"></span>
		<ul id="nav">
			<li id="home" class="active"><a href="/"><span class="fi-home"></span> Home</a></li>
			<li id="settings" class="more">
				<a href="/settings"><span class="fi-widget"></span> Settings<span class="arrow-down"></span></a>
				<ul>
					<li><a href="#"><span class="fi-wrench"></span> Server Settings</a></li></li>
					<li><a href="#"><span class="fi-torso"></span> Edit Profile</a></li></li>
				</ul>
			</li>
			<li id="help" class="more">
				<a href="#"><span class="fi-plus"></span> Help<span class="arrow-down"></span></a></span>
				<ul>
					<li><a href="#"><span class="fi-ticket"></span> Create Support Ticket</a></li></li>
					<li><a href="#"><span class="fi-megaphone"></span> Contact Support</a></li>
					<li><a href="#"><span class="fi-list-thumbnails"></span> FAQ</a></li></li>
				</ul>
			</li>
			<li id="logout"><a href="/logout"><span class="fi-power"></span> Logout</a></li>
		</ul>
	</div>
</nav>
