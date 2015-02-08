import openerp
from openerp import http, api
from openerp.http import Controller, route, request


class gfe_server(Controller):
	@route('/servers', type='http', auth='public', website=True)
	def index(self, *args, **kw):
		return "wup"