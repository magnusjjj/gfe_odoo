import openerp
from openerp import http, api
from openerp.http import Controller, route, request
import sys, traceback, re
import werkzeug.utils
from openerp.addons.web.controllers.main import ensure_db
from openerp.addons.auth_signup.controllers.main import AuthSignupHome

def set_cookie_and_redirect(redirect_url):
    redirect = werkzeug.utils.redirect(redirect_url, 303)
    redirect.autocorrect_location_header = False
    return redirect

class gfe_signup(openerp.addons.web.controllers.main.Home):
	@route('/', type='http', auth='public', website=True)
	def index(self, *args, **kw):
		ensure_db()
		
		
		
		# Get the request parameters:
		qcontext = request.params.copy()
		
		# Grab a list of all the countries in the database
		Countries = request.env["res.country"]
		User = request.env['res.users']
		
		# Shove them into our big ball of variables
		qcontext["countries"] = Countries.search([])
		
		# Check if we are supposed to try to register a new user:
		
		errors = []
		
		if request.httprequest.method == 'POST':
			errors = self.tryreg(qcontext)
		
		
		# This is not the prettiest thing i have done, rather the result of two days of debugging:
		# Logs the user in, if appropriate.
		# This dirty hack exist because you cant login to a user you have created in the same request. Bah.
		
		if "doredirect" in errors:
			request.session.gfe_login = errors["login"]
			request.session.gfe_password = errors["password"]
			return http.redirect_with_hash("/?dologin=true")
		
		
		if qcontext.get("dologin") is not None:
			# We need to auth, only the superuser can auth.
			request.uid = openerp.SUPERUSER_ID
			# Autenticate..
			uid = http.request.session.authenticate(request.session.db, request.session.gfe_login, request.session.gfe_password)
			
			request.session.gfe_login = request.session.gfe_password = ''
			
			# This is just so that the username in the template 'looks right', so it doesnt look like we are logged in as admin..
			request.uid = uid
			request.session.uid = uid
			
			if uid is not False:
				return http.redirect_with_hash("/web")
			else:
				pass 
				
		# Shove possible errors from the registration into our big bag of variables:
		
		qcontext['errors'] = errors
		qcontext['haserrors'] = len(errors) > 0
		
		# And render the view! Woo!
		
	#	if request.httprequest.method == 'POST' and len(errors) == 0:
	#		return set_cookie_and_redirect("/?login=" +qcontext.get("login")+"&password="+qcontext.get("password"))
	#	else:
		return request.render('gfe_signup.index', qcontext);
		
	def tryreg(self, qcontext):
		
		# Make a variable to hold all the errors in...
		errors = []
		
		# Make a list of all the fields we cant stand being empty.. :P
		notempty = {"x_country": "Country","x_firstname": "First name", "x_surname": "Surname", "password": "Password",
		"x_adress": "Adress", "x_zipcode": "Zipcode", "x_birthdate": "Birthdate",
		"x_city": "City", "x_phone": "Phone", "login": "Email", "x_accept1": "Accept 1", "x_accept2": "Accept 2", "x_accept3": "Accept 3"}
		
		# Loop through them
		for field in notempty:
			if qcontext.get(field) is None or qcontext.get(field).strip() == "":
				# And begin setting errors
				errors.append("The field \"" + notempty[field] + "\" must not be empty")
		
		# Check the email adress...
		emailcheck = re.compile("^[^@]*@(.*)$")
		if emailcheck.match(qcontext.get("login")) is None:
			errors.append("Check the Email field, that does not look like an Email adress.")
		
		# Check the birthdate...
		datecheck = re.compile("^[0-9]{4}\\-[0-9]{2}\\-[0-9]{2}$")
		if datecheck.match(qcontext.get("x_birthdate")) is None:
			errors.append("Check the Birthdate field, the format should be YYYY-MM-DD.")
		
		# Check the password length...
		if(len(qcontext.get("password")) < 8):
			errors.append("Your password needs to be at least 8 characters long.")
		
		# If its a swedish personnummer, check that its valid:
		personkoll = re.compile("^[0-9]{6}\\-[0-9]{4}$")
		personnummer = qcontext.get("x_socialsecuritynumber")
		
		if qcontext.get("x_country") == "198":
			if personkoll.match(personnummer) is not None:
				sum = 0
				n = 2
				
				personnummer = personnummer[:6] + personnummer[7:]
				for i in range(0,9):
					
					tmp = int(personnummer[i]) * n
					
					if (tmp > 9):
						sum += 1 + ((tmp % 10))
					else:
						sum += tmp
					if n == 2:
						n = 1
					else:
						n = 2
				if ((sum + int(personnummer[9])) % 10) != 0:
					errors.append("Your Swedish social security number is incorrect. Please double check.")
				else:
					pass
			else:
				errors.append("Your Swedish social security number is specified in the wrong format. The correct format is YYMMDD-XXXX")
		
		# Now, we need to make a member, which is called a 'partner' in odoo
		
		partnerparams = {
			"birthdate": qcontext.get("x_birthdate"),
			"city": qcontext.get("x_city"),
			"contact_address": qcontext.get("x_adress"),
			"country_id": qcontext.get("x_country"),
			"zip": qcontext.get("x_zipcode"),
			"phone": qcontext.get("x_phone"),
			"street": qcontext.get("x_adress"),
			"display_name": qcontext.get("x_firstname") + ' ' + qcontext.get("x_surname"),
			"x_firstname": qcontext.get("x_firstname"),
			"x_surname": qcontext.get("x_surname"),
			"x_socialsecuritynumber": qcontext.get("x_socialsecuritynumber"),
			"x_careof": qcontext.get("x_careof"),
			"email": qcontext.get("login").lower(),
			"mobile": qcontext.get("x_other_phone"),
			"name": qcontext.get("x_firstname") + ' ' + qcontext.get("x_surname")
		}
		
		# And a user for that partner...
		
		userparams = {
			"partner_id": '',
			"display_name": qcontext.get("x_firstname") + ' ' + qcontext.get("x_surname"),
			"login": qcontext.get("login").lower(),
			"new_password": qcontext.get("password")
		}
		
		# Grab the database models...
		
		Partner = request.env['res.partner']
		User = request.env['res.users']
		

		# And try to create the partner and user
		if len(errors) == 0:
			try:
				mypartner = Partner.sudo().create(partnerparams)
				user = None
				try:
					userparams["partner_id"] = mypartner.id
					myuser = User.sudo().with_context({"no_reset_password":True}).create(userparams) 
					if myuser.id is not None:
						#mypartner.sudo().send_greeting(myuser)
						return {"doredirect": True, "login": qcontext.get("login").lower(), "password": qcontext.get("password")}
						#errors.append("blub")
				except Exception, e:
					errors.append("Error in user creation:" + repr(e))
					pass
			except Exception, e:
				errors.append("Error in member creation")
				pass
		return errors