# Importamos las librerías necesarias para el uso de la API
import pandas as pd 
import numpy as np
import sklearn
from fastapi import FastAPI
from sklearn.feature_extraction.text import CountVectorizer 
from sklearn.neighbors import NearestNeighbors

# Indicamos título y descripción de la API
app = FastAPI(title='PROYECTO INDIVIDUAL Nº1 -Machine Learning Operations (MLOps)',
            description='API de datos y recomendaciones de películas basado en machine learning')

# Se importan los datasets que se van a usar
df = pd.read_csv('movies_ok_1.csv')
df1 = pd.read_csv('movies_machine_learning.csv')


# Función para dar la bienvenida al sistema de recomendacion
@app.get('/')
async def index():
    return {'Bienvenido a la API de recomedación y consulta de peliculas. Por favor dirigite a /docs'}

@app.get('/about/')
async def about():
    return {'PROYECTO INDIVIDUAL Nº1 -Machine Learning Operations (MLOps)'}

# Funcion de consulta de la cantidad de peliculas por mes
@app.get('/peliculas_mes/{mes}')
def peliculas_mes(mes):

    mes = mes.lower()
    meses = {
    'enero': 1,
    'febrero': 2,
    'marzo': 3,
    'abril': 4,
    'mayo': 5,
    'junio': 6,
    'julio': 7,
    'agosto': 8,
    'septiembre': 9,
    'octubre': 10,
    'noviembre': 11,
    'diciembre': 12}

    mes_numero = meses[mes]

    # Convertir la columna "fecha" a un objeto de tipo fecha
    df['release_date'] = pd.to_datetime(df['release_date'])


    try:
        month_filtered = df[df['release_date'].dt.month == mes_numero]
    except (ValueError, KeyError, TypeError):
        return None

    month_unique = month_filtered.drop_duplicates(subset='id')
    respuesta = month_unique.shape[0]

    return {'mes':mes, 'cantidad':respuesta}

# Funcion de consulta de peliculas por dia de la semana 
@app.get('/peliculas_dis/{dia}')
def peliculas_dia(dia):

    days = {
    'lunes': 'Monday',
    'martes': 'Tuesday',
    'miercoles': 'Wednesday',
    'jueves': 'Thursday',
    'viernes': 'Friday',
    'sabado': 'Saturday',
    'domingo': 'Sunday'}

    day = days[dia.lower()]

    lista_peliculas_day = df[df['release_date'].dt.day_name() == day].drop_duplicates(subset='id')
    cantidad = lista_peliculas_day.shape[0]

    return {'dia': dia, 'cantidad': cantidad}

# Funcion de consulta del numero de colecciones de peliculas, su ganancia total y ganancia promedio 
@app.get('/franquicia/{franquicia}')
def franquicia(franquicia):

    lista_pelis_franquicia = df[(df['collection'] == franquicia)].drop_duplicates(subset='id')

    cantidad_pelis_franq = (lista_pelis_franquicia).shape[0]
    revenue_franq = lista_pelis_franquicia['revenue'].sum()
    promedio_franq = revenue_franq/cantidad_pelis_franq

    return {'franquicia':franquicia, 'cantidad':cantidad_pelis_franq, 'ganancia_total':revenue_franq, 'ganancia_promedio':promedio_franq}

# Funcion de consulta del numero de peliculas por pais 
@app.get('/peliculas_pais/{pais}')
def peliculas_pais(pais):
    # Selecciona todas las películas del DataFrame 'df' cuya columna 'country' contiene el país especificado.
    # La función lambda se utiliza para aplicar la operación a cada valor de la columna 'country'.
    peliculas_pais = df[df['country'].apply(lambda x: pais in str(x) if pd.notnull(x) else False)]
    
    # Elimina las filas duplicadas de la película para evitar contar varias veces una misma película.
    peliculas_pais = peliculas_pais.drop_duplicates(subset='id')
    
    # Cuenta la cantidad de películas restantes después de eliminar los duplicados.
    respuesta = len(peliculas_pais)
    
    # Devuelve los resultados en un diccionario con claves legibles.
    return {'pais': pais, 'cantidad de peliculas': respuesta}

# Funcion de consulta del numero de peliculas por productora, ganancias totales y numero de peliculas
@app.get('/productoras/{productora}')
def productoras(productora):

    lista_pelis_productoras = df[(df['company'] == productora)].drop_duplicates(subset='id')

    cantidad_pelis_prod = (lista_pelis_productoras).shape[0]
    revenue_prod = lista_pelis_productoras['revenue'].sum()


    return {'productora':productora, 'ganancia_total':revenue_prod, 'cantidad':cantidad_pelis_prod}

# Funcion de consulta de peliculas, su inversion, ganancias, retorno y año
@app.get('/retorno/{pelicula}')
def retorno(pelicula):
    info_pelicula = df[(df['title'] == pelicula)].drop_duplicates(subset='title')
    pelicula_nombre = info_pelicula['title'].iloc[0]
    inversion_pelicula = str(info_pelicula['budget'].iloc[0])
    ganancia_pelicula = str(info_pelicula['revenue'].iloc[0])
    retorno_pelicula = str(info_pelicula['return'].iloc[0])
    year_pelicula = str(info_pelicula['release_year'].iloc[0])

    return {'pelicula':pelicula_nombre, 'inversion':inversion_pelicula, 'ganacia':ganancia_pelicula,'retorno':retorno_pelicula, 'anio':year_pelicula}

# PARAMETROS PARA LA EJECUCION DE LA FUNCION DE RECOMENDACION BASADA EN MACHINE LEARNING

#  En esta matriz, cada fila representa una película y cada columna 
# representa un termino en las caracteristicas combinadas
cv = CountVectorizer(stop_words='english', max_features=5000)
count_matrix = cv.fit_transform(df1['tags'])

# Creamos un modelo para encontrar los vecinos mas cercanos en un espacio de caracterisicaa
nn = NearestNeighbors(metric='cosine', algorithm='brute')
nn.fit(count_matrix)

# Creamos un indice de titulos de peliculas y eliminamos los duplicados
indices = pd.Series(df1.index, index=df1['title']).drop_duplicates()


@app.get("/recomendacion/{titulo}")
def recomendacion(title: str):
    '''Ingresas un nombre de pelicula y te recomienda las similares en una lista
    ''' 
    # Verifica si el titulo ingresado se encuentra en el df
    if title not in df1['title'].values:
        return 'La pelicula no se encuentra en el conjunto de la base de datos.'
    else:
        # Si el título esta en el df, encuentra su indice
        index = indices[title]

        # Obtiene las puntuaciones de similitud de las 5 peliculas más cercanas
        distances, indices_knn = nn.kneighbors(count_matrix[index], n_neighbors=6)  # indica que queremos encontrar las 6 peliculas más similares, incluyendo la pelicula dada

        # Obtiene los indices de las peliculas
        movie_indices = indices_knn[0][1:]  # Se omite el primer indice (la pelicula misma) con [1:]

        # Devuelve las 5 peliculas mas similares
        return df1['title'].iloc[movie_indices].tolist()
    




