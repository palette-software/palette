# -*- coding: utf-8 -*-
<%inherit file="layout.mako" />

<%block name="title">
<title>Palette - Activity</title>
</%block>

<section class="secondary-side-bar">
  <a class="Psmall-only" id="toggle-events" href="#"><i class="fa"></i></a>
  <h2>Filter</h2>
  <h5 class="sub margin-top">Workbook Name</h5>
  <section class="padding">
    <input type="text" placeholder="example" value="Workbook Name">
  </section>
  <h5 class="sub">Project</h5>
  <div class="btn-group">
    <button type="button" class="btn btn-default dropdown-toggle" data-toggle="dropdown"><div>All Projects</div><span class="caret"></span>
    </button>
    <ul class="dropdown-menu" role="menu">
      <li><a href="#">All Projects</a></li>
      <li><a href="#">Annual Reports</a></li>
      <li><a href="#">Quarterly Reports</a></li>
    </ul>
  </div>
  <h5 class="sub">Publisher</h5>
  <div class="btn-group">
    <button type="button" class="btn btn-default dropdown-toggle" data-toggle="dropdown"><div>All Publishers</div><span class="caret"></span>
    </button>
    <ul class="dropdown-menu" role="menu">
      <li><a href="#">All Publishers</a></li>
      <li><a href="#">John Abdo</a></li>
      <li><a href="#">Matthew Laue</a></li>
    </ul>
  </div>
</section>

<section class="dynamic-content">
  <section class="top-zone">
    <section class="row">
      <section class="col-xs-12">
        <h1 class="page-title">Workbook Archive</h1>
        <a class="Psmallish-only" id="toggle-event-filters" href="#"><i class="fa fa-angle-left"></i></a>
      </section>
    </section>
    <section class="row">
      <section class="col-xs-12">
        <div class="btn-group">
          <button type="button" class="btn btn-default dropdown-toggle" data-toggle="dropdown"><div>All Sites</div><span class="caret"></span>
          </button>
          <ul class="dropdown-menu" role="menu">
            <li><a href="#">All Sites</a></li>
            <li><a href="#">Finance</a></li>
            <li><a href="#">Marketing</a></li>
          </ul>
        </div>
      </section>
    </section>
  </section>
  <section class="row bottom-zone">
    <section class="col-lg-12">
      <article class="event">
        <i class="fa fa-fw fa-book red"></i>
        <h3>Served Accessed</h3>
        <p>Bixly Production Server --- <span>5:03 am</span><span> 4/14/2014</span></p>
        <div>
          Bixly Production Server has completed a lorem ipsum text placeholder words. Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum 
        </div>
      </article>
      <article class="event">
        <i class="fa fa-fw fa-book"></i>
        <h3>Eastern Region Quarterly Sales Report.twbx</h3>
        <p>John Abdo</p>
        <div>
          <a href="#">05:30 PM PDT on May 1, 2014</a> by John Abdo<br/>
	      <a href="#">02:17 PM PDT on April 14, 2014</a> by Matthew Laue <a href="#"><i class="fa fa-fw fa-pencil edit"></i></a>
        </div>
      </article>
      <article class="event">
        <i class="fa fa-fw fa-book"></i>
        <h3>Restoration initializated on Xepler Production Server #2</h3>
        <p>Bixly Production Server --- <span>5:03 am</span><span> 4/14/2014</span></p>
        <div>
          Bixly Production Server has completed a lorem ipsum text placeholder words. Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum 
        </div>
      </article>
      <article class="event">
        <i class="fa fa-fw fa-book"></i>
        <h3>Served Accessed</h3>
        <p>Bixly Production Server --- <span>5:03 am</span><span> 4/14/2014</span></p>
        <div>
          Bixly Production Server has completed a lorem ipsum text placeholder words. Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum 
        </div>
      </article>
      <article class="event">
        <i class="fa fa-fw fa-book"></i>
        <h3>Served Accessed</h3>
        <p>Bixly Production Server --- <span>5:03 am</span><span> 4/14/2014</span></p>
        <div>
          Bixly Production Server has completed a lorem ipsum text placeholder words. Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum 
        </div>
      </article>
      <article class="event">
        <i class="fa fa-fw fa-book"></i>
        <h3>Served Settings Modified</h3>
        <p>Bixly Production Server --- <span>5:03 am</span><span> 4/14/2014</span></p>
        <div>
          Bixly Production Server has completed a lorem ipsum text placeholder words. Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum 
        </div>
      </article>
      <article class="event">
        <i class="fa fa-fw fa-book"></i>
        <h3>Served Accessed</h3>
        <p>Bixly Production Server --- <span>5:03 am</span><span> 4/14/2014</span></p>
        <div>
          Bixly Production Server has completed a lorem ipsum text placeholder words. Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum 
        </div>
      </article>
      <article class="event">
        <i class="fa fa-fw fa-book"></i>
        <h3>Served Accessed</h3>
        <p>Bixly Production Server --- <span>5:03 am</span><span> 4/14/2014</span></p>
        <div>
          Bixly Production Server has completed a lorem ipsum text placeholder words. Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum 
        </div>
      </article>
      <article class="event">
        <i class="fa fa-fw fa-book"></i>
        <h3>Backup Started</h3>
        <p>Bixly Production Server --- <span>5:03 am</span><span> 4/14/2014</span></p>
        <div>
          Bixly Production Server has completed a lorem ipsum text placeholder words. Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum 
        </div>
      </article>
      <article class="event">
        <i class="fa fa-fw fa-book"></i>
        <h3>Restoration initializated on Xepler Production Server #2</h3>
        <p>Bixly Production Server --- <span>5:03 am</span><span> 4/14/2014</span></p>
        <div>
          Bixly Production Server has completed a lorem ipsum text placeholder words. Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum 
        </div>
      </article>
      <article class="event">
        <i class="fa fa-fw fa-book"></i>
        <h3>Served Accessed</h3>
        <p>Bixly Production Server --- <span>5:03 am</span><span> 4/14/2014</span></p>
        <div>
          Bixly Production Server has completed a lorem ipsum text placeholder words. Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum 
        </div>
      </article>
      <article class="event">
        <i class="fa fa-fw fa-book"></i>
        <h3>Served Accessed</h3>
        <p>Bixly Production Server --- <span>5:03 am</span><span> 4/14/2014</span></p>
        <div>
          Bixly Production Server has completed a lorem ipsum text placeholder words. Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum 
        </div>
      </article>
      <article class="event">
        <i class="fa fa-fw fa-book"></i>
        <h3>Served Accessed</h3>
        <p>Bixly Production Server --- <span>5:03 am</span><span> 4/14/2014</span></p>
        <div>
          Bixly Production Server has completed a lorem ipsum text placeholder words. Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum 
        </div>
      </article>
      <article class="event">
        <i class="fa fa-fw fa-book"></i>
        <h3>Served Accessed</h3>
        <p>Bixly Production Server --- <span>5:03 am</span><span> 4/14/2014</span></p>
        <div>
          Bixly Production Server has completed a lorem ipsum text placeholder words. Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum 
        </div>
      </article>
    </section>
  </section>
</section>

<script src="/app/module/palette/js/vendor/require.js" data-main="/app/module/palette/js/common.js">

</script>
