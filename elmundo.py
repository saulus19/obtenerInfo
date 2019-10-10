from _ssl import SSLError
import logging
import requests
from bs4 import BeautifulSoup
import articulo
import pickle
from time import sleep
import sqlalchemy as db
from sqlalchemy.sql import func, distinct, select, and_
from sqlalchemy.orm import sessionmaker
from sqlalchemy import desc
import traceback
import sys
logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)


# Web Scrapes transcript data from blog
def url_to_transcript(url):
    '''Obtener los enlaces del blog de Hernan Casciari.'''
    try:
        enlaces = []
        page = requests.get(url).text
        soup = BeautifulSoup(page, "lxml")
        print('URL', url)
        for a in soup.find_all(class_='ue-c-cover-content__link', href=True):
            print("Found link:", a['href'])
            enlaces.append(a['href'])
        # sleep(0.75) #damos tiempo para que no nos penalice un firewall
        enlaces = set(enlaces)
        enlaces = list(enlaces)
    except Exception:
        try:
            for a in soup.find_all(class_='flex-article', href=True):
                enlaces.append(a['href'])

        except Exception:
            return ''
    return enlaces


base = ['https://www.elmundo.es', 'https://www.elmundo.es/economia', 'https://www.elmundo.es/economia/ahorro-y-consumo.html',
        'https://www.elmundo.es/economia/macroeconomia.html',
        'https://www.elmundo.es/economia/empresas.html', 'https://www.elmundo.es/economia/bolsa/indices.html',
        'https://www.elmundo.es/economia/vivienda.html',
        'https://www.elmundo.es/economia/innovadores.html', 'https://elmundo.es',
        'https://www.elmundo.es/tecnologia.html', 'https://www.elmundo.es/television.html',
        'https://www.elmundo.es/cultura.html', 'https://www.elmundo.es/espana.html']

# , 'https://elmundo.es', 'http://www.expansion.com']
urls = base
print(len(urls))

# Recorrer las URLs y obtener los enlaces
enlaces = list()
for u in urls:
    enlaces.extend(url_to_transcript(u))

print('Articulos en portada', len(enlaces))

# en enlace tengo los artículos candidatos
articulos = []
masenlaces = []
totalenlaces = 0

Session = sessionmaker()
engine = db.create_engine('mysql+pymysql://root:test@localhost/prensa', pool_pre_ping=True,
                          pool_recycle=3600)
# engine = db.create_engine('mysql+mysqldb://pcs001:Saulus19072003.@192.168.1.2/prensa', pool_pre_ping=True,
#                           pool_recycle=3600)
connection = engine.connect()
Session.configure(bind=engine)
sesion = Session()
metadata = db.MetaData()
art = db.Table('articulo', metadata, autoload=True, autoload_with=engine)


def reduce_url(u):
    pos = u.find('.html')
    u2 = u
    if pos != -1:
        u2 = u[:pos + 5]
    return u2


results = connection.execute(db.select([art.c.url]))
enlaces_tratados = []
for row in results:
    enlaces_tratados.append(reduce_url(row.url))

# idArticulo += 1
for u in enlaces:
    # Vamos a calcular hasta el *.html' del enlace
    if not str(u).startswith('htt'):
        if not str(u).startswith('//'):
            u = '/' + '/'
            if not str(u).startswith('//'):
                u =  '/' + u
        u = "https:" + u
    if reduce_url(u) not in enlaces_tratados:
        # if (u.startswith('http://www.elmundo.es') or u.startswith('https://www.elmundo.es'))\
        if not u.endswith('.pdf'):
                # and not u.startswith('https://www.elmundo.es/blogs')\
            print (u)
            enlaces_tratados.append(reduce_url(u))
            # print('Tratando ', u)
            totalenlaces += 1
            a = articulo.Articulo(reduce_url(u))
            if a.valido:

                for v in a.enlaces_internos:
                    if v not in enlaces:
                        enlaces.append(v)
                articulos.append(a)
                # idArticulo += 1
                print('Tratados ', len(articulos), ' artículos - Total Articulos ', len(enlaces), ' Total enlaces: ',
                      totalenlaces, 'Tratado: ', u)
                try:
                    query = db.insert(art).values(url=a.url, titulo=a.titulo, cuerpo=a.contenido,
                                                  origen=1, fecha_articulo=a.fecha_articulo, procesado=False)
                                                  # ,pagina=a.pagina.encode('cp1252'))
                    ResultProxy = connection.execute(query)
                except Exception:
                    print('Error al insertar: ', u)
                    print(Exception)
                    exc_info = sys.exc_info()
                    traceback.print_exception(*exc_info)
            else:
                for v in a.enlaces_internos:
                   if v not in enlaces:
                        enlaces.append(v)
                print('Descartado: %s Total enlaces %s' % (u, len(enlaces)))
#    else:
# print('*** Enlace tratado previamente: ', u)

print('Total de artículos ', len(articulos))
print('Enlaces totales ', len(enlaces))
