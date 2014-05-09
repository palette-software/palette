# -*- coding: utf-8 -*-
<%inherit file="configure.mako" />

<%block name="title">
    <title>Palette - Profile</title>
</%block>

<section class="dynamic-content config-content">
    <section class="top-zone">
        <h1 class="page-title">Profile</h1>
    </section>
    <section class="row bottom-zone">
        <section class="col-sm-12 col-md-8 col-lg-6">
            <label>Profile Info</label>
            <input type="text" name="firstname" placeholder="First Name" />
            <input type="text" name="lastname" placeholder="Last Name" />
            <input type="email" name="email" placeholder="Email Name" />
            <input type="email" name="username" placeholder="Tableau Username" />
            <label>Admin Type</label>
            <div class="btn-group">
              <button type="button" class="btn btn-default dropdown-toggle" data-toggle="dropdown"><div>No Administrator Access</div><span class="caret"></span>
              </button>
              <ul class="dropdown-menu" role="menu">
                <li><a href="#">No Administrator Access</a></li>
                <li><a href="#">No Change Administrator Access</a></li>
                <li><a href="#">Full Change Administrator Access</a></li>
              </ul>
            </div>
            <label>Location Info</label>
            <div class="btn-group">
              <button type="button" class="btn btn-default dropdown-toggle" data-toggle="dropdown"><div>Time Zone</div><span class="caret"></span>
              </button>
              <ul class="dropdown-menu" role="menu">
                <li><a href="#">(GMT -12:00) Eniwetok, Kwajalein</a></li>
                <li><a href="#">(GMT -12:00) Eniwetok, Kwajalein</a></li>
                <li><a href="#">(GMT -12:00) Eniwetok, Kwajalein</a></li>
              </ul>
            </div>
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
</section>
