from akiri.framework.api import RESTApplication

class PaletteRESTHandler(RESTApplication):

    def base_path_info(self, req):
        # REST handlers return the handle path prefix too, strip it.
        path_info = req.environ['PATH_INFO']
        if path_info.startswith('/' + self.NAME):
            path_info = path_info[len(self.NAME)+1:]
        if path_info.startswith('/'):
            path_info = path_info[1:]
        return path_info
