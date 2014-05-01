# -*- coding: utf-8 -*- 
<%inherit file="configure.mako" />

<%block name="title">
<title>Palette - Configure - Profile</title>
</%block>

<section class="dynamic-content">
  <section class="top-zone">
    <h1 class="page-title">Configure</h1>
  </section>
  <section class="row bottom-zone">
    <div class="profile-settings-content col-xs-12 col-lg-10">
      <div class="content active" id="profile">
        <section class="row">
          <section class="col-sm-12 col-md-8 col-lg-6">
            <label>Profile Info</label>
	    <input type="text" name="firstname" placeholder="First Name" />
	    <input type="text" name="lastname" placeholder="Last Name" />
	    <input type="email" name="email" placeholder="Email Name" />
	    <input type="email" name="username" placeholder="Tableau Username" />
	    <label>Admin Type</label>
	    <label class="select">
	      <select class="styled-select">
		<option>No Administrator Access</option>
		<option>No Change Administrator Access</option>
		<option>Full Change Administrator Access</option>
	      </select>
	    </label>
	    <label>Location Info</label>
	    <label class="select">
	      <select class="styled-select" name="DropDownTimezone" id="DropDownTimezone">
		<option>Select Time Zone</option>
		<option value="-12.0">(GMT -12:00) Eniwetok, Kwajalein</option>
		<option value="-11.0">(GMT -11:00) Midway Island, Samoa</option>
		<option value="-10.0">(GMT -10:00) Hawaii</option>
		<option value="-9.0">(GMT -9:00) Alaska</option>
		<option value="-8.0">(GMT -8:00) Pacific Time (US &amp; Canada)</option>
		<option value="-7.0">(GMT -7:00) Mountain Time (US &amp; Canada)</option>
		<option value="-6.0">(GMT -6:00) Central Time (US &amp; Canada), Mexico City</option>
		<option value="-5.0">(GMT -5:00) Eastern Time (US &amp; Canada), Bogota, Lima</option>
		<option value="-4.0">(GMT -4:00) Atlantic Time (Canada), Caracas, La Paz</option>
		<option value="-3.5">(GMT -3:30) Newfoundland</option>
		<option value="-3.0">(GMT -3:00) Brazil, Buenos Aires, Georgetown</option>
		<option value="-2.0">(GMT -2:00) Mid-Atlantic</option>
		<option value="-1.0">(GMT -1:00 hour) Azores, Cape Verde Islands</option>
		<option value="0.0">(GMT) Western Europe Time, London, Lisbon, Casablanca</option>
		<option value="1.0">(GMT +1:00 hour) Brussels, Copenhagen, Madrid, Paris</option>
		<option value="2.0">(GMT +2:00) Kaliningrad, South Africa</option>
		<option value="3.0">(GMT +3:00) Baghdad, Riyadh, Moscow, St. Petersburg</option>
		<option value="3.5">(GMT +3:30) Tehran</option>
		<option value="4.0">(GMT +4:00) Abu Dhabi, Muscat, Baku, Tbilisi</option>
		<option value="4.5">(GMT +4:30) Kabul</option>
		<option value="5.0">(GMT +5:00) Ekaterinburg, Islamabad, Karachi, Tashkent</option>
		<option value="5.5">(GMT +5:30) Bombay, Calcutta, Madras, New Delhi</option>
		<option value="5.75">(GMT +5:45) Kathmandu</option>
		<option value="6.0">(GMT +6:00) Almaty, Dhaka, Colombo</option>
		<option value="7.0">(GMT +7:00) Bangkok, Hanoi, Jakarta</option>
		<option value="8.0">(GMT +8:00) Beijing, Perth, Singapore, Hong Kong</option>
		<option value="9.0">(GMT +9:00) Tokyo, Seoul, Osaka, Sapporo, Yakutsk</option>
		<option value="9.5">(GMT +9:30) Adelaide, Darwin</option>
		<option value="10.0">(GMT +10:00) Eastern Australia, Guam, Vladivostok</option>
		<option value="11.0">(GMT +11:00) Magadan, Solomon Islands, New Caledonia</option>
		<option value="12.0">(GMT +12:00) Auckland, Wellington, Fiji, Kamchatka</option>
	      </select>
	    </label>
	    <section class="row margin-top">
	      <section class="col-xs-12 col-sm-6">
		<button type="submit" name="save" class="p-btn p-btn-blue">Save</button>
	      </section>
	      <section class="col-xs-12 col-sm-6">
		<!-- ONLY SHOW AFTER SAVE IS PRESSED <button type="submit" name="revert" class="p-btn p-btn-grey"><span class="fi-refresh"></span> Revert</button>
		     </section>-->
	      </section>
            </section>
          </section>
        </section>
      </div>
    </div>
  </section>
</section>

<script type="text/javascript">

	var hash = window.location.hash;

	if (hash) {

		$('.profile-settings-content .content, .profile-settings-nav dd').removeClass('active');
		$('.profile-settings-content .content'+hash+'').addClass('active');
	}
	
	$('.profile-settings-nav dd a').bind('click', function(e) {
		e.preventDefault();
	    hash = $(this).attr("href");

	    if (window.location.hash == hash) {
	    	return false;
	    }

	    window.location = hash;

		$('.profile-settings-content .content, .profile-settings-nav dd').removeClass('active');
		$('.profile-settings-content .content'+hash+'').addClass('active');
	});

	$('.profile-settings-nav dd').bind('click', function() {
		$(this).addClass('active');
	});
	
</script>
