from pyramid.config import Configurator
from pepxml.resources import Root

def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    config = Configurator(root_factory=Root, settings=settings)
    config.add_view('pepxml.views.my_view',
                    context='pepxml:resources.Root',
                    renderer='pepxml:templates/mytemplate.pt')
    config.add_static_view('static', 'pepxml:static', cache_max_age=3600)
    return config.make_wsgi_app()
