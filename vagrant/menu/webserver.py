#webserver.py
import re
import cgi
import pdb

from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Restaurant, Base, MenuItem


class RestaurantController(object):
	'''Not a real controller, but enough separation for a quick course. We still could improve on how to use the model'''
	
	def __init__(self):
		# Put here the values to create a new session to the db
		self.engine = create_engine('sqlite:///restaurantmenu.db')
		# Bind the engine to the metadata of the Base class so that the
		# declaratives can be accessed through a DBSession instance
		Base.metadata.bind = self.engine
		DBSession = sessionmaker(bind=self.engine)
		# Get a session
		self.dbsession = DBSession()

	def get_restaurants(self):
		'''Gets all the retaurants'''
		return self.dbsession.query(Restaurant).all()

	def get_restaurant(self, id):
		'''Gets a single restaurant by id'''
		return self.dbsession.query(Restaurant).get(id)

	def delete_restaurant(self, id):
		'''Deletes a restaurant'''
		restaurant = self.get_restaurant(id)
		if(restaurant):
			self.dbsession.delete(restaurant)
			self.dbsession.commit()
		return restaurant

	def update_restaurant(self, restaurant):
		'''Updates the restaurant and returns the item'''
		# Map the db object with the in memory object
		dbObject = self.dbsession.query(Restaurant).get(restaurant.id)
		dbObject.name = restaurant.name
		self.dbsession.add(dbObject)
		self.dbsession.commit()
		return dbObject

	def add_restaurant(self, restaurant):
		'''Adds a restaurant to the db'''
		self.dbsession.add(restaurant)
		self.dbsession.commit()
		return restaurant


class RestaurantView(object):
	'''Not a real view, since it has some logic. But handles enough separation for this course'''

	def __init__(self):
		'''Instantiates the controller. Which we will use to handle the logic'''

		self.controller = RestaurantController()

	def get_restaurants(self, message = ''):
		'''Returns all the restaurants using some basic html'''
		restaurants = self.controller.get_restaurants()

		html = '''
			<html>
				<body>
					%s
					<a href="/restaurants/new">Add restaurant</a>
					<h2>List of restaurants: </h2>
					%s
				</body>
			</html>'''

		restaurants_str = ''

		for restaurant in restaurants:
			restaurants_str += '''
				<p> 
					<span class="title"> %s </span> -  
					<a href='/restaurant/%s/edit'> Edit </a> 
					<a href='/restaurant/%s/delete'> Delete </a>
				</p>''' % (restaurant.name, restaurant.id, restaurant.id)

		return html % (message, restaurants_str)


	def edit_restaurant(self, id=None, restaurant=None, update=False):
		'''Edits the restaurant and returns a simple page'''
		
		if(update):
			restaurant = self.controller.update_restaurant(restaurant)

		id = id or (restaurant and restaurant.id)
		restaurant = restaurant or self.controller.get_restaurant(id)

		html = '''
				<html>
					<body>
						<a href="/restaurants" >View all restaurants</a>						
			'''

		if restaurant:
			html += '''
							<h1>%s</h1>
							<form method='POST' enctype='multipart/form-data' action='/restaurant/%s/edit/'>
								<input name="id" type="hidden" value="%s"/>
								<input name="name" type="text" value="%s"/>
								<input name="submit" type="submit" value="Edit Restaurant" />
								<a href="/restaurant/%s/delete"> Delete restaurant</a>
							</form>''' % (restaurant.name, restaurant.id, restaurant.id, restaurant.name, restaurant.id)

		html += '''
					</body>
				</html>
				'''
		return html

	def delete_restaurant(self, id):
		'''Deletes the restaurant'''
		restaurant = self.controller.delete_restaurant(id)
		html_msg = '' if not restaurant else '''<h3>The restaurant %s has been deleted </h3> </hr>''' % restaurant.name
		html = self.get_restaurants(html_msg)
		return html


	def add_restaurant(self, restaurant=None):
		'''Adds a new restaurant if one is given'''
		if(restaurant):
			restaurant = self.controller.add_restaurant(restaurant)

		added_html = '' if not restaurant else ('''<h3>Restaurant %s added successfully</h3></hr>''' % restaurant.name)

		html = '''
		<html>
			<body>
				%s
				<h2> Add a restaurant </h2>
				<form method='POST' enctype='multipart/form-data' action='/restaurants/new'>
					<input name="name" type="text" value="" />
					<input name="submit" type="submit" />
				</form>

				<a href="/restaurants"> View all restaurants</a>
			</body>
		</html>
		''' % added_html

		return html



class WebserverHandler(BaseHTTPRequestHandler):
	'''Building on top of BaseHTTPRequestHandler. The course later on should use some framework. Lets hope it is django'''
	
	def add_headers(self, code=200):
		self.send_response(code)
		self.send_header('Content-type', 'text/html')

	def get_form(self):
		'''Part of the given code. Not useful in the restaurants solution'''
		return '''
			<form method='POST' enctype='multipart/form-data' action='/hello'>
				<h2> What would you like me to say?</h2>
				<input name='message' type='text' />
				<input name='submit' type='submit' value='GO' />
			</form> 
			'''

	def do_GET(self):

		view = RestaurantView()

		try:
			
			edit_match = re.match(r'^/restaurant/(\d+)/edit/?$', self.path) 
			delete_match = re.match(r'^/restaurant/(\d+)/delete/?$', self.path) 

			self.add_headers()

			if self.path.endswith('/favicon.ico'):
				output = ''

			elif self.path.endswith('/hello'):
				output = '<html><body>Hello!%s</body></html>' % self.get_form()

			elif self.path.endswith('/hola'):
				output = '<html><body>Hola!%s</body></html>' % self.get_form()				

			elif self.path.endswith('/restaurants'):
				output = view.get_restaurants()
			elif edit_match:
				param = edit_match.group(1)
				output = view.edit_restaurant(id=param)
			elif delete_match:
				param = delete_match.group(1)
				output = view.delete_restaurant(param)
			elif self.path.endswith('/restaurants/new'):
				output = view.add_restaurant()
			else:
				output = 'Probably I dont exist'

			print output
			self.end_headers()
			self.wfile.write(output)

		except IOError:
			self.send_error(404, 'File not found %s', self.path)


	def do_POST(self):

		view = RestaurantView()

		try:
			self.add_headers(301)
			ctype, pdict = cgi.parse_header(self.headers.getheader('content-type'))
			if ctype == 'multipart/form-data':
				fields = cgi.parse_multipart(self.rfile, pdict)


			edit_match = re.match(r'^/restaurant/(\d+)/edit/?$', self.path) 
			delete_match = re.match(r'^/restaurant/(\d+)/delete/?$', self.path) 

			if (self.path.endswith('/hello')):
				messagecontent = fields.get('message')

				output = '''
					<html>
						<body>
							<h2>Okay, how about this:</h2>
							<h1>%s</h1>
							%s 
						</body>
					</html>
					''' % (messagecontent[0], self.get_form())
			elif self.path.endswith('/hola'):
				messagecontent = fields.get('message')

				output = '''
					<html>
						<body>
							<h2>Okay, how about this:</h2>
							<h1>%s</h1>
							%s 
						</body>
					</html>
					''' % (messagecontent[0], self.get_form())
			elif edit_match: 
				restaurant = Restaurant()
				restaurant.id = fields.get('id')[0]
				restaurant.name = fields.get('name')[0]
				output = view.edit_restaurant(restaurant = restaurant, update=True)
			elif self.path.endswith('/restaurants/new'):
				self.send_header('Location', '/restaurants')
				restaurant = Restaurant()
				restaurant.name = fields.get('name')[0]
				output = view.add_restaurant(restaurant)
			else:
				output = 'Probably I dont exist'

			self.end_headers()
			self.wfile.write(output)

		except IOError:
			self.send_error(404, 'File not found %s', self.path)





def main():
	try:
		port = 9900
		server = HTTPServer(('', port), WebserverHandler)
		print "Web server is running on port %s" % port
		server.serve_forever()
	except KeyboardInterrupt:
		print "^C entered, stopping web server..."
		server.socket.close()



if __name__ == '__main__':
	main()
