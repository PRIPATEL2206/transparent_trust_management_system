from .services import ConfigService


def site_config_context(request):
    if request.path.startswith(('/static/', '/media/', '/health/', '/robots.txt')):
        return {}
    config = ConfigService.get_config()
    return {'site_config': config}
