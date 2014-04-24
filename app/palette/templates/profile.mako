# -*- coding: utf-8 -*- 
<%inherit file="_layout.mako" />

<%block name="title">
<title>Palette - Configure</title>
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

</%block>
<%include file="side-bar.mako" />
<section class="dynamic-content">
  <section class="top-zone">
      <h1 class="page-title">Configure</h1>
  </section>
  <section class="row bottom-zone">
    <dl class="profile-settings-nav col-sm-12 col-lg-2">
    	<div>
    		<dd class="active"><a href="#profile">My Profile</a></dd>
	        <dd><a href="#organization">Organization</a></dd>
	        <dd><a href="#backup">Backup</a></dd>
	        <dd><a href="#systemmonitor">System Monitor</a></dd>
	        <dd><a href="#billing">Billing</a></dd>
    	</div>
    </dl>
      <div class="profile-settings-content col-xs-12 col-lg-10">
        <div class="content active" id="profile">
          <section class="row">
          	<section class="col-sm-12 col-md-8 col-lg-6">

          		  <label>Profile Info</label>
				  <input type="text" name="firstname" placeholder="First Name">
				  <input type="text" name="lastname" placeholder="Last Name">
				  <input type="email" name="email" placeholder="Email Name">
				  <input type="email" name="username" placeholder="Tableau Username">
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
          <section class="col-sm-12 col-md-4 col-lg-3">
      		<label class="text-center margin-top">Profile Pic</label>
      		<a href="#"><img class="profile-pic" src="/app/module/palette/images/blankuser.png"></a><br>
      		<button type="submit" name="save" class="p-btn p-btn-dark-grey">Add Image</button>
      	</section>         
        </div>
        <div class="content" id="organization">
          <label>Organization Name</label>
		  <input type="text" name="organizationinput">
		  <label>Admin Users</label>
		  <ul class="user-list">
		  	<li><img src="/app/module/palette/images/blankuser.png"><h4>David Olsen</h4><h5>david@xepler.com</h5><span class="fi-x"></span></li>
		  	<li><img src="/app/module/palette/images/blankuser.png"><h4>Jeremy Venegas</h4><h5>jeremy@xepler.com</h5><span class="fi-x"></span></li>
		  	<li><div class="add-user"><span class="fa fa-fw fa-plus"></span></div><h5>Add new via email</h5></li>
		  </ul>
		  <section class="row margin-top">
            <section class="col-xs-12 col-sm-6"><button type="submit" name="save" class="p-btn p-btn-blue">Save</button></section>
            <section class="col-xs-12 col-sm-6"><!-- ONLY SHOW AFTER SAVE IS PRESSED <button type="submit" name="revert" class="p-btn p-btn-grey"><span class="fi-refresh"></span> Revert</button></section>-->
           </section>
        </div>
        <div class="content" id="backup">
          <label>Recurring backup</label>
	      <input type="radio" name="backupinput" value="Yes" id="backupYes"><label for="backupYes" class="radio-label"><span></span> Yes</label>
	      <input type="radio" name="backupinput" value="No" id="backupNo"><label for="backupNo" class="radio-label"><span></span> No</label>
          <label>Scheduled Time</label>
          <section class="row">
            <section class="col-sn-12 col-md-4">
	            <label class="select">
				  <select class="styled-select">
				  	<option>1</option>
				  	<option>2</option>
				  	<option>3</option>
				  	<option>4</option>
				  	<option>5</option>
				  	<option>6</option>
				  	<option>7</option>
				  	<option>8</option>
				  	<option>9</option>
				  	<option>10</option>
				  	<option>11</option>
				  	<option>12</option>
				  </select>
			    </label>	
            </section>
            <section class="col-sn-12 col-md-4">
            	<label class="select">
				  <select class="styled-select">
				  	<option>00</option>
				  	<option>15</option>
				  	<option>30</option>
				  	<option>45</option>
				  </select>
			    </label>	
            </section>
            <section class="col-sn-12 col-md-4">
            	<label class="select">
				  <select class="styled-select">
				  	<option>AM</option>
				  	<option>PM</option>
				  </select>
			    </label>	
            </section>
           </section>
           <label>Frequency (Hours)</label>
           <label class="select">
				  <select class="styled-select">
				  	<option>1</option>
				  	<option>2</option>
				  	<option>3</option>
				  	<option>4</option>
				  	<option>5</option>
				  	<option>6</option>
				  	<option>7</option>
				  	<option>8</option>
				  	<option>9</option>
				  	<option>10</option>
				  	<option>11</option>
				  	<option>12</option>
				  	<option>13</option>
				  	<option>14</option>
				  	<option>15</option>
				  	<option>16</option>
				  	<option>17</option>
				  	<option>18</option>
				  	<option>19</option>
				  	<option>20</option>
				  	<option>21</option>
				  	<option>22</option>
				  	<option>23</option>
				  	<option>24</option>
				  </select>
			    </label>
          <section class="row margin-top">
            <section class="col-xs-12 col-sm-6"><button type="submit" name="save" class="p-btn p-btn-blue">Save</button></section>
            <section class="col-xs-12 col-sm-6"><!-- ONLY SHOW AFTER SAVE IS PRESSED <button type="submit" name="revert" class="p-btn p-btn-grey"><span class="fi-refresh"></span> Revert</button></section>-->
           </section>
        </div>
        <div class="content" id="systemmonitor">
          <label>Email Notifications</label>
          <p class="italic-label">Add people to be notified</p>
          <ul class="user-list">
		  	<li><img src="/app/module/palette/images/blankuser.png"><h4>David Olsen</h4><h5>david@xepler.com</h5><span class="fi-x"></span></li>
		  	<li><div class="add-user"><span class="fa fa-fw fa-plus"></span></div><h5>Add new via email</h5></li>
		  </ul>
          <section class="row margin-top">
            <section class="col-xs-12 col-sm-6"><button type="submit" name="save" class="p-btn p-btn-blue">Save</button></section>
            <section class="col-xs-12 col-sm-6"><!-- ONLY SHOW AFTER SAVE IS PRESSED <button type="submit" name="revert" class="p-btn p-btn-grey"><span class="fi-refresh"></span> Revert</button></section>-->
           </section>
        </div>
        <div class="content" id="billing">
          <label>Card Info</label>
		  <input type="text" name="cardnumber" placeholder="Credit Card Number">
		  <input type="text" name="cardname" placeholder="Name on Card">
          <label class="select">
			  <select class="styled-select">
			  	<option>Card Type</option>
			  </select>
		  </label>
		  <section class="row">
			<section class="col-xs-6">
			  <input type="text" name="expdate" placeholder="Exp. Date (mm/dd/yyyy)">				
            </section>
            <section class="col-xs-6">
              <input type="text" name="cvc" placeholder="CVC">	
            </section>
          </section>
           <label>Billing Address</label>
           <input type="text" name="address" placeholder="Address">
           <section class="row">
			<section class="col-xs-12 col-md-6">
			  <input type="text" name="state" placeholder="State">
			  <input type="text" name="zip" placeholder="Zip Code">				
            </section>
            <secton class="col-xs-12 col-md-6">
              <input type="text" name="city" placeholder="City">
              <label class="select">
				  <select class="styled-select">
				  	<option>Country</option>
				  	<option value="AF">Afghanistan</option>
					<option value="AX">Åland Islands</option>
					<option value="AL">Albania</option>
					<option value="DZ">Algeria</option>
					<option value="AS">American Samoa</option>
					<option value="AD">Andorra</option>
					<option value="AO">Angola</option>
					<option value="AI">Anguilla</option>
					<option value="AQ">Antarctica</option>
					<option value="AG">Antigua and Barbuda</option>
					<option value="AR">Argentina</option>
					<option value="AM">Armenia</option>
					<option value="AW">Aruba</option>
					<option value="AU">Australia</option>
					<option value="AT">Austria</option>
					<option value="AZ">Azerbaijan</option>
					<option value="BS">Bahamas</option>
					<option value="BH">Bahrain</option>
					<option value="BD">Bangladesh</option>
					<option value="BB">Barbados</option>
					<option value="BY">Belarus</option>
					<option value="BE">Belgium</option>
					<option value="BZ">Belize</option>
					<option value="BJ">Benin</option>
					<option value="BM">Bermuda</option>
					<option value="BT">Bhutan</option>
					<option value="BO">Bolivia, Plurinational State of</option>
					<option value="BQ">Bonaire, Sint Eustatius and Saba</option>
					<option value="BA">Bosnia and Herzegovina</option>
					<option value="BW">Botswana</option>
					<option value="BV">Bouvet Island</option>
					<option value="BR">Brazil</option>
					<option value="IO">British Indian Ocean Territory</option>
					<option value="BN">Brunei Darussalam</option>
					<option value="BG">Bulgaria</option>
					<option value="BF">Burkina Faso</option>
					<option value="BI">Burundi</option>
					<option value="KH">Cambodia</option>
					<option value="CM">Cameroon</option>
					<option value="CA">Canada</option>
					<option value="CV">Cape Verde</option>
					<option value="KY">Cayman Islands</option>
					<option value="CF">Central African Republic</option>
					<option value="TD">Chad</option>
					<option value="CL">Chile</option>
					<option value="CN">China</option>
					<option value="CX">Christmas Island</option>
					<option value="CC">Cocos (Keeling) Islands</option>
					<option value="CO">Colombia</option>
					<option value="KM">Comoros</option>
					<option value="CG">Congo</option>
					<option value="CD">Congo, the Democratic Republic of the</option>
					<option value="CK">Cook Islands</option>
					<option value="CR">Costa Rica</option>
					<option value="CI">Côte dIvoire</option>
					<option value="HR">Croatia</option>
					<option value="CU">Cuba</option>
					<option value="CW">Curaçao</option>
					<option value="CY">Cyprus</option>
					<option value="CZ">Czech Republic</option>
					<option value="DK">Denmark</option>
					<option value="DJ">Djibouti</option>
					<option value="DM">Dominica</option>
					<option value="DO">Dominican Republic</option>
					<option value="EC">Ecuador</option>
					<option value="EG">Egypt</option>
					<option value="SV">El Salvador</option>
					<option value="GQ">Equatorial Guinea</option>
					<option value="ER">Eritrea</option>
					<option value="EE">Estonia</option>
					<option value="ET">Ethiopia</option>
					<option value="FK">Falkland Islands (Malvinas)</option>
					<option value="FO">Faroe Islands</option>
					<option value="FJ">Fiji</option>
					<option value="FI">Finland</option>
					<option value="FR">France</option>
					<option value="GF">French Guiana</option>
					<option value="PF">French Polynesia</option>
					<option value="TF">French Southern Territories</option>
					<option value="GA">Gabon</option>
					<option value="GM">Gambia</option>
					<option value="GE">Georgia</option>
					<option value="DE">Germany</option>
					<option value="GH">Ghana</option>
					<option value="GI">Gibraltar</option>
					<option value="GR">Greece</option>
					<option value="GL">Greenland</option>
					<option value="GD">Grenada</option>
					<option value="GP">Guadeloupe</option>
					<option value="GU">Guam</option>
					<option value="GT">Guatemala</option>
					<option value="GG">Guernsey</option>
					<option value="GN">Guinea</option>
					<option value="GW">Guinea-Bissau</option>
					<option value="GY">Guyana</option>
					<option value="HT">Haiti</option>
					<option value="HM">Heard Island and McDonald Islands</option>
					<option value="VA">Holy See (Vatican City State)</option>
					<option value="HN">Honduras</option>
					<option value="HK">Hong Kong</option>
					<option value="HU">Hungary</option>
					<option value="IS">Iceland</option>
					<option value="IN">India</option>
					<option value="ID">Indonesia</option>
					<option value="IR">Iran, Islamic Republic of</option>
					<option value="IQ">Iraq</option>
					<option value="IE">Ireland</option>
					<option value="IM">Isle of Man</option>
					<option value="IL">Israel</option>
					<option value="IT">Italy</option>
					<option value="JM">Jamaica</option>
					<option value="JP">Japan</option>
					<option value="JE">Jersey</option>
					<option value="JO">Jordan</option>
					<option value="KZ">Kazakhstan</option>
					<option value="KE">Kenya</option>
					<option value="KI">Kiribati</option>
					<option value="KP">Korea, Democratic Peoples Republic of</option>
					<option value="KR">Korea, Republic of</option>
					<option value="KW">Kuwait</option>
					<option value="KG">Kyrgyzstan</option>
					<option value="LA">Lao Peoples Democratic Republic</option>
					<option value="LV">Latvia</option>
					<option value="LB">Lebanon</option>
					<option value="LS">Lesotho</option>
					<option value="LR">Liberia</option>
					<option value="LY">Libya</option>
					<option value="LI">Liechtenstein</option>
					<option value="LT">Lithuania</option>
					<option value="LU">Luxembourg</option>
					<option value="MO">Macao</option>
					<option value="MK">Macedonia, the former Yugoslav Republic of</option>
					<option value="MG">Madagascar</option>
					<option value="MW">Malawi</option>
					<option value="MY">Malaysia</option>
					<option value="MV">Maldives</option>
					<option value="ML">Mali</option>
					<option value="MT">Malta</option>
					<option value="MH">Marshall Islands</option>
					<option value="MQ">Martinique</option>
					<option value="MR">Mauritania</option>
					<option value="MU">Mauritius</option>
					<option value="YT">Mayotte</option>
					<option value="MX">Mexico</option>
					<option value="FM">Micronesia, Federated States of</option>
					<option value="MD">Moldova, Republic of</option>
					<option value="MC">Monaco</option>
					<option value="MN">Mongolia</option>
					<option value="ME">Montenegro</option>
					<option value="MS">Montserrat</option>
					<option value="MA">Morocco</option>
					<option value="MZ">Mozambique</option>
					<option value="MM">Myanmar</option>
					<option value="NA">Namibia</option>
					<option value="NR">Nauru</option>
					<option value="NP">Nepal</option>
					<option value="NL">Netherlands</option>
					<option value="NC">New Caledonia</option>
					<option value="NZ">New Zealand</option>
					<option value="NI">Nicaragua</option>
					<option value="NE">Niger</option>
					<option value="NG">Nigeria</option>
					<option value="NU">Niue</option>
					<option value="NF">Norfolk Island</option>
					<option value="MP">Northern Mariana Islands</option>
					<option value="NO">Norway</option>
					<option value="OM">Oman</option>
					<option value="PK">Pakistan</option>
					<option value="PW">Palau</option>
					<option value="PS">Palestinian Territory, Occupied</option>
					<option value="PA">Panama</option>
					<option value="PG">Papua New Guinea</option>
					<option value="PY">Paraguay</option>
					<option value="PE">Peru</option>
					<option value="PH">Philippines</option>
					<option value="PN">Pitcairn</option>
					<option value="PL">Poland</option>
					<option value="PT">Portugal</option>
					<option value="PR">Puerto Rico</option>
					<option value="QA">Qatar</option>
					<option value="RE">Réunion</option>
					<option value="RO">Romania</option>
					<option value="RU">Russian Federation</option>
					<option value="RW">Rwanda</option>
					<option value="BL">Saint Barthélemy</option>
					<option value="SH">Saint Helena, Ascension and Tristan da Cunha</option>
					<option value="KN">Saint Kitts and Nevis</option>
					<option value="LC">Saint Lucia</option>
					<option value="MF">Saint Martin (French part)</option>
					<option value="PM">Saint Pierre and Miquelon</option>
					<option value="VC">Saint Vincent and the Grenadines</option>
					<option value="WS">Samoa</option>
					<option value="SM">San Marino</option>
					<option value="ST">Sao Tome and Principe</option>
					<option value="SA">Saudi Arabia</option>
					<option value="SN">Senegal</option>
					<option value="RS">Serbia</option>
					<option value="SC">Seychelles</option>
					<option value="SL">Sierra Leone</option>
					<option value="SG">Singapore</option>
					<option value="SX">Sint Maarten (Dutch part)</option>
					<option value="SK">Slovakia</option>
					<option value="SI">Slovenia</option>
					<option value="SB">Solomon Islands</option>
					<option value="SO">Somalia</option>
					<option value="ZA">South Africa</option>
					<option value="GS">South Georgia and the South Sandwich Islands</option>
					<option value="SS">South Sudan</option>
					<option value="ES">Spain</option>
					<option value="LK">Sri Lanka</option>
					<option value="SD">Sudan</option>
					<option value="SR">Suriname</option>
					<option value="SJ">Svalbard and Jan Mayen</option>
					<option value="SZ">Swaziland</option>
					<option value="SE">Sweden</option>
					<option value="CH">Switzerland</option>
					<option value="SY">Syrian Arab Republic</option>
					<option value="TW">Taiwan, Province of China</option>
					<option value="TJ">Tajikistan</option>
					<option value="TZ">Tanzania, United Republic of</option>
					<option value="TH">Thailand</option>
					<option value="TL">Timor-Leste</option>
					<option value="TG">Togo</option>
					<option value="TK">Tokelau</option>
					<option value="TO">Tonga</option>
					<option value="TT">Trinidad and Tobago</option>
					<option value="TN">Tunisia</option>
					<option value="TR">Turkey</option>
					<option value="TM">Turkmenistan</option>
					<option value="TC">Turks and Caicos Islands</option>
					<option value="TV">Tuvalu</option>
					<option value="UG">Uganda</option>
					<option value="UA">Ukraine</option>
					<option value="AE">United Arab Emirates</option>
					<option value="GB">United Kingdom</option>
					<option value="US">United States</option>
					<option value="UM">United States Minor Outlying Islands</option>
					<option value="UY">Uruguay</option>
					<option value="UZ">Uzbekistan</option>
					<option value="VU">Vanuatu</option>
					<option value="VE">Venezuela, Bolivarian Republic of</option>
					<option value="VN">Viet Nam</option>
					<option value="VG">Virgin Islands, British</option>
					<option value="VI">Virgin Islands, U.S.</option>
					<option value="WF">Wallis and Futuna</option>
					<option value="EH">Western Sahara</option>
					<option value="YE">Yemen</option>
					<option value="ZM">Zambia</option>
					<option value="ZW">Zimbabwe</option>
				  </select>
		  	  </label>
            </section>
            <label>Contact Info</label>
	           <input type="text" name="fullname" placeholder="Full Name">
			   <input type="text" name="phonenumber" placeholder="Phone Number (123-123-1234)">	
			   <input type="email" name="email" placeholder="Email">
	          <section class="row margin-top">
	            <section class="col-xs-12 col-sm-6"><button type="submit" name="save" class="p-btn p-btn-blue">Save</button></section>
	            <section class="col-xs-12 col-sm-6"><!-- ONLY SHOW AFTER SAVE IS PRESSED <button type="submit" name="revert" class="p-btn p-btn-grey"><span class="fi-refresh"></span> Revert</button></section>-->
	          </section>
	        </section>
        </div>
      </div>
  </section>
</section>
		

<%include file="commonjs.mako" />

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