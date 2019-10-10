from datetime import datetime
from bs4 import BeautifulSoup
import requests
import requests.exceptions
from nltk.corpus import stopwords
import string


class Articulo:

    # __non_words.extend(map(str, range(10)))
    def __init__(self, url):
        self._url = ""
        self._titulo = ""
        self._contenido = ""
        self._fecha_proceso = datetime.now()
        self._fecha_articulo = ""
        self._origen = ""
        self._sw = stopwords.words('spanish')
        self._url = url
        self._non_words = list(string.punctuation)
        self._non_words.extend(['¿', '¡'])
        self._non_words.extend(map(str, range(10)))
        self._enlaces_internos = list()
        self._pagina = ""
        self._valido = True
        try:
            self._pagina = requests.get(url).text
        except Exception:
            self._pagina = ""
            self._valido = False

    @property
    def url(self):
        return self._url

    @property
    def titulo(self):
        if self._titulo == '':
            self._titulo = self._obtener_titulo_articulo()
        return self._titulo

    @property
    def fecha_proceso(self):
        return self._fecha_proceso

    @property
    def contenido(self):
        if self._contenido == '':
            self._contenido = self._obtener_contenido_articulo()
        return self._contenido

    @property
    def enlaces_internos(self):
        if len(self._enlaces_internos) == 0:
            self._enlaces_internos = list()
        return self._enlaces_internos

    @property
    def pagina(self):
        return self._pagina
    @property
    def fecha_articulo(self):
        if self._fecha_articulo == '':
            self._fecha_articulo = self._obtener_fecha_publicacion()
            try:
                self._fecha_articulo = datetime.strptime(self._fecha_articulo, '%Y-%m-%dT%H:%M:%SZ')

            except ValueError:
                self._fecha_articulo = datetime.now()
                print('Error en la fecha:%s', self._fecha_articulo)

        return self._fecha_articulo

    @property
    def valido(self):
        self._enlaces_internos = self._obtener_enlaces_internos()
        if self._valido:
            self._contenido = self._obtener_contenido_articulo()
        if self._valido:
            self._titulo = self._obtener_titulo_articulo()
        return self._valido

    def _prepara_texto(self, texto):
        return texto
        """
        texto = texto.translate("".maketrans("áéíóúÁÉÍÓÚ", "aeiouAEIOU"))
        tokens = [t for t in texto.split()]
        for token in tokens:
            if token in self.__sw:
                tokens.remove(token)
        table = str.maketrans('', '', string.punctuation)
        stripped = [w.translate(table) for w in tokens]
        # texto = texto.translate(string.maketrans("",""), texto.translate(self.__non_words), "")
        texto = " ".join(str(x) for x in stripped)
        return texto
        """

    def _quita_acentos(self, texto):
        texto = texto.translate("".maketrans("áéíóú", "aeiou"))
        return texto

    def _obtener_titulo_articulo(self):
        """
        Obtiene el título del artículo
        :param texto: contenido del artículo
        :return: título del artículo
        """
        try:
            soup = BeautifulSoup(self._pagina, "lxml")
            text = soup.h1.string
            text = text.lower()
            # text = self.__prepara_texto(text)
        except Exception:
            #print('ERROR, no se puede encontrar el titulo del artículo')
            self._valido = True
            return 'NaN'
        return text

    def _obtener_contenido_articulo(self):
        try:
            soup = BeautifulSoup(self._pagina, "lxml")
            extraido = [p.text for p in soup.find_all('p')]
            text = ''.join(extraido)
            text = text.lower()
            # text = self.__prepara_texto(text)
        except Exception:
            print('ERROR, al obtener el contenido del artículo')
            self._valido = False
            return ''
        return text

    def _obtener_enlaces_internos(self):
        """
        Obtiene los enlaces que existen dentro del artículo
        :return: enlaces que hay dentro de un artículo
        """
        try:
            enlaces_internos = []
            soup = BeautifulSoup(self._pagina, "lxml")
            enlaces = soup.find_all("a", href=True)
            for a in enlaces:
                enlaces_internos.append(a['href'])
            enlaces_a_devolver = []
            # para devolver enlaces únicos
            for u in enlaces_internos:
                if u not in enlaces_a_devolver:
                    enlaces_a_devolver.append(u)
        except Exception:
            print('ERROR al obtener los enlaces internos', self._url)
            self.__valido = True
            return []

        return enlaces_a_devolver

    def _obtener_fecha_publicacion(self):
        # ue - c - article__publishdate
        try:
            soup = BeautifulSoup(self._pagina, "lxml")
            fecha = soup.find(class_='ue-c-article__publishdate')
            if fecha == None:
                fecha = soup.find(class_='datePublished')
            fecha = fecha.find('time')
            if fecha.has_attr('datetime'):
                fecha = fecha['datetime']
        except Exception:
            print('ERROR, fecha no encontrada en el articulo')
            self._valido = True
            return ''
        return fecha
