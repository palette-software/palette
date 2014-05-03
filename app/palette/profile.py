import os

from akiri.framework.api import RESTApplication
from akiri.framework.config import store

from paste import fileapp
from webob import exc

from controller.meta import Session
from controller.profile import UserProfile

from configure import ConfigureRenderer

class Profile(ConfigureRenderer):
    TEMPLATE = "profile.mako"
    configure_active = 'profile'

def make_profile(global_conf):
    return Profile(global_conf)

class ProfileApplication(RESTApplication):
    # The REST applications will be available at "/rest/profile",
    # "/rest/profile/photo", etc.
    NAME = 'profile'

    def __init__(self, global_conf):
        super(ProfileApplication, self).__init__(global_conf)

        palette_dir = store.get("palette", "dir", default="/var/palette")
        self.photodir = palette_dir + os.sep + "data" + os.sep + "photos"

        self.default_photo = store.get("palette", "default_photo",
                                                        default="blankuser.png")

    def handle(self, req):
        if not 'REMOTE_USER' in req.environ:
            raise exc.HTTPBadRequest()

        if req.environ['PATH_INFO'] == '/profile':
            return self.handle_profile(req)
        elif req.environ['PATH_INFO'] == '/profile/photo':
            return self.handle_photo(req)
        raise exc.HTTPBadRequest()

    ###### handle /rest/profile
    def handle_profile_POST(self, req):
        raise exc.HTTPBadRequest()

    def handle_profile_GET(self, req):
        user_name = req.environ['REMOTE_USER']
        user_profile = UserProfile.get_by_name(user_name)

        if not user_profile:
            return {}

        self.profile = {}
        # Convert db entry into a dictionary
        for key in ['userid', 'name', 'first_name', 'last_name', 'email',
                                        'photo', 'tableau_username', 'gmt']:
            self.profile[key] = getattr(user_profile, key)

        # Add a list of roles the user has
        self.profile['roles'] = []
        for role in user_profile.roles:
            self.profile['roles'].append(role.name)

        return self.profile

    def handle_profile(self, req):
        if req.method == 'POST':
            return self.handle_profile_POST(req)
        elif req.method == 'GET':
            return self.handle_profile_GET(req)
        raise exc.HTTPBadRequest()

    ###### handle /rest/profile/photo
    def handle_photo_POST(self, req):
        user_name = req.environ['REMOTE_USER']
        user_profile = UserProfile.get_by_name(user_name)

        if not user_profile:
            raise exc.HTTPNotFound()

        upload = req.POST.get("file", None)
        if upload is None:
            raise exc.HTTPBadRequest()

        ignored, extension = os.path.splitext(upload.filename)

        if not extension:
            # Filename must have an extension
            print "photo filename must have an extension"
            raise exc.HTTPBadRequest()

        photo_filename = str(user_profile.userid) + extension

        full_path = self.photodir + os.sep + photo_filename

        # Save by userid.extension
        with open(full_path, "w") as fd:
            fd.write(upload.file.read())

        # Remember the photo filename in the db
        session = Session()
        user_profile.photo = photo_filename
        session.commit()

        return { 'path': photo_filename }

    def handle_photo_GET(self, req):
        user_name = req.environ['REMOTE_USER']
        user_profile = UserProfile.get_by_name(user_name)
        if not user_profile:
            print "no such user:", user_name
            raise exc.HTTPBadRequest()

        photo_filename = user_profile.photo
        if not photo_filename:
            photo_filename = self.default_photo

        photo_path = self.photodir + os.sep + photo_filename

        if not os.path.exists(photo_path):
            print "Missing photo filename:", photo_path
            raise exc.HTTPNotFound()

        print "returning contents of:", photo_path
        return fileapp.FileApp(photo_path)

    def handle_photo(self, req):
        if req.method == 'POST':
            return self.handle_photo_POST(req)
        elif req.method == 'GET':
            return self.handle_photo_GET(req)
        raise exc.HTTPBadRequest()
