#!/usr/bin/env python3
import os
import tornado.ioloop
import tornado.web
import tornado.log
import json
import requests
import datetime

from models import weathertable

from jinja2 import \
  Environment, PackageLoader, select_autoescape

ENV = Environment(
  loader=PackageLoader('weather', 'templates'),
  autoescape=select_autoescape(['html', 'xml'])
)

class TemplateHandler(tornado.web.RequestHandler):
  def render_template (self, tpl, context):
    template = ENV.get_template(tpl)
    self.write(template.render(**context))

def retrieve_api_data(cityname):
   url = "http://api.openweathermap.org/data/2.5/weather"
   querystring = {"q": cityname,"APIKEY":"2e32ce8e4192c1446ca78334f23e1ecb","units":"imperial"}
   headers = {
        'cache-control': "no-cache",
        'postman-token': "16ca84d0-4102-9b21-8f21-a9acd570d842"
        }

   response = requests.request("GET", url, headers=headers, params=querystring)
   # print(response.text)

   weatherdata = weathertable.create(
   cityname=cityname,
   weatherdata=response.json()
    )
   # print('api_call',type(weatherdata))
   return weatherdata


class MainHandler(TemplateHandler):
  def get (self):
    self.set_header('Cache-Control',
     'no-store, no-cache, must-revalidate, max-age=0')
    self.render_template("index.html", {})


  def post (self):
    cityname = self.get_body_argument('cityname')
    cityname = cityname.title()
    print(cityname)

    old = datetime.datetime.utcnow() - datetime.timedelta(minutes=15)

    try:
        weather = weathertable.select().where(weathertable.cityname == cityname).where(weathertable.stampcreated >= old).get()
        # print('try block', weather, type(weather))

    except:
        # import traceback              use import traceback to find errors
        # traceback.print_exc()         when using try/except
        # print('except block')
        weather = retrieve_api_data(cityname)
        # print(weather)

    self.render_template('results.html', {'response': weather})

class LocationHandler (TemplateHandler):
    def post(self):
        x_real_ip = self.request.headers.get("X-Forwarded-For")
        remote_ip = x_real_ip or self.request.remote_ip
        url = f'http://ipinfo.io/{remote_ip}/json'
        if remote_ip.startswith(('192.', '127.', '10.', "::1")):
            url = 'http://ipinfo.io/json'

        # print('this is your ip' + remote_ip + url)

        print(url, self.request.headers)
        response = requests.get(url)

        data = json.loads(response.text)
        print(data)
        # print('\n\n', data, '\n\n')
        city = data['city']
        weather = retrieve_api_data(city)
        # print('location ', weather, type(weather))

        template = ENV.get_template('results.html')
        self.write(template.render({'response': weather}))


def make_app():
  return tornado.web.Application([
    (r"/", MainHandler),
    (r"/location", LocationHandler),
    (r"/static/(.*)",
      tornado.web.StaticFileHandler, {'path': 'static'}),
  ], autoreload=True)

if __name__ == "__main__":
  tornado.log.enable_pretty_logging()
  app = make_app()
  app.listen(int(os.environ.get('PORT', '8080')))
  print('Port 8080 is good to go')
  tornado.ioloop.IOLoop.current().start()
