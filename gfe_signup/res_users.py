from openerp import models,fields,api,http

# In odoo, its possible to extend things like the user table.
# All you need to do is name your model the same as the system model.
# and write _inherit with the same name. Its pretty neat.

class res_users(models.Model):
	_inherit = 'res.users'
	
	def gfe_login(self, db, uid_in, password_in):
		return http.request.session.authenticate(http.request.session.db, uid_in, password=password_in)
		
		

class res_partner(models.Model):
	_inherit = 'res.partner'
	
	x_socialsecuritynumber = fields.Char(default="")
	x_firstname = fields.Char(default="")
	x_surname = fields.Char(default="")
	x_careof = fields.Char(default="")
	
	
	def send_greeting(self,user):
		template = self.env['ir.model.data'].get_object('gfe_signup', 'gfe_register_email')
		raise Exception(self.env['email.template'].send_mail(template.id, user.id, force_send=True, raise_exception=True))