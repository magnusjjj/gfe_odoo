from openerp import models,fields,api,http

class gfe_server(models.Model):
	_name = 'gfe.server'
	_inherit = 'mail.thread'
	name = fields.Char(default="")
	description = fields.Text(default="")
	color = fields.Integer() 
	howto = fields.Text(default="")
	admin_id = fields.Many2many('res.users', ondelete='set null', string="Admins", index=True)
	operator_id = fields.Many2many('res.users', ondelete='set null', string="Operators", index=True)
	image = fields.Binary()
	image_medium = fields.Binary()
	image_small = fields.Binary()
	
	def action_follow(self, cr, uid, ids, context=None):
		return self.message_subscribe_users(cr, uid, ids, context=context)
	
	def action_unfollow(self, cr, uid, ids, context=None):
		return self.message_unsubscribe_users(cr, uid, ids, context=context)