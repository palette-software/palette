<nav id="mainNav" data-topbar>
	<div class="container">
		<%include file="_logo.mako" />
		<span id="toggle-main-menu" class="fi-list"></span>
		<ul class="nav nav-profile">
			<li class="more" id="profile-link">
				<a href="/profile"><h4>John, Abdo</h4><h5>Full Admin</h5> <img src="/app/module/palette/images/blankuser.png"></a>
				<ul>
					<li><a href="/profile"><span class="fi-torso"></span> My Profile</a></li>
					<li id="logout"><a href="/logout"><span class="fi-power"></span> Logout</a></li>
				</ul>
			</li>
		</ul>
		<ul class="nav menu">
			<li id="home" class="active-home"><a href="/"><span class="fi-home"></span> Home</a></li>
			<li id="settings" class="active-profile">
				<a href="/profile"><span class="fi-widget"></span> Configure</a>
			</li>
			<li id="help" class="more active-help">
				<a href="#"><span class="fi-plus"></span> Help<span class="arrow-down"></span></a>
				<ul>
					<li><a href="/support/ticket"><span class="fi-ticket"></span> Create Support Ticket</a></li></li>
					<li><a href="/support/contact"><span class="fi-megaphone"></span> Contact Support</a></li>
				</ul>
			</li>
			<li class="small-only" id="logout"><a href="/logout"><span class="fi-power"></span> Logout</a></li>
		</ul>
		
	</div>
</nav>
