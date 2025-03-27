from flask import Flask, render_template, render_template_string, request, jsonify
import sqlite3
import folium
from folium.plugins import MarkerCluster, HeatMap, HeatMapWithTime
import pandas as pd
import haversine
import json
import plotly.express as px
import plotly
import plotly.graph_objects as go
from faker import Faker
from faker.providers import date_time, BaseProvider

# DATABASE
# définir une base de données SQLITE
###
DATABASE = r'\mesures.db'

#coordonnées Sherbrooke et Radius pour la génération aléatoire de lon/lat
latSh = 45.41 
latRad = 0.11
lonSh = -71.95
lonRad = 0.15

# nombre de données fictives désirées
nb_values = 2500

## Réinitialisation de la base de données
def initdb():
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        # créer une table points si elle n'existe pas
        cursor.execute('DROP TABLE IF EXISTS mesures')
        cursor.execute(
            'CREATE TABLE IF NOT EXISTS mesures (id INTEGER PRIMARY KEY AUTOINCREMENT, lat REAL, lon REAL, date DATE, year INT, month INT, day INT, type TEXT, val1 REAL, val2 REAL, val3 REAL)'
        )
        conn.commit()
        ajouterMesures(nb_values)

# ajouter des mesures à la base de données
def insertMeasures(liste):
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.executemany("""INSERT INTO mesures (lat, lon, date, year, month, day, type, val1, val2, val3) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", liste)
        conn.commit()

# créer des mesures fictives
def ajouterMesures(qty):
    list_mesures = []
    Faker.seed(0) #pour avoir toujours les mêmes résultats dans les tests, enlever ou changer pour avoir données différentes
    for i in range(qty):
        lat = (float(fake.coordinate(center = latSh, radius = latRad)))
        lon = (float(fake.coordinate(center = lonSh, radius = lonRad)))
        date = Faker('fr_CA').date_between(start_date = '-5y', end_date = 'now')
        datesql = date.strftime('%Y-%m-%d')
        year = date.year
        month = date.month
        day = date.day
        type = Faker('fr_CA').random_element(elements=('A', 'B', 'C', 'D', 'E', 'F', 'G', 'H'))
        val1 = fake.random_int(min = 0, max = 100)
        val2 = fake.random_int(min = 100, max = 500)  
        val3 = fake.random_int(min = 1, max = 10000)/10000
        mesure = (lat, lon, datesql,year, month, day, type, val1, val2, val3)
        list_mesures.append(mesure)
    insertMeasures(list_mesures)


# Fonction pour récupérer toutes les mesures
def getAllPoints():
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM mesures')
        rows = cursor.fetchall()
    return rows

# Fonction pour récupérer les mesures dans un radius autour d'un point
# Utilise présentement haversine
# À explorer : utiliser une BD spatiale plutot que sqlite et faire requete spatiale st_distance
def getPointsRange(position, distance) :
    rows = getAllPoints()
    filtered_rows = []
    position = (position[0], position[1])
    for row in rows:
        position2 = (row[1], row[2])
        if haversine.haversine(position, position2) <= distance/1000:
            filtered_rows.append(row)
    return filtered_rows


# Fonction pour créer une requete SQL
def getIndicator(indicator, where, groupby, orderby):
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute("""SELECT id, year, month, day, type, {indicator} FROM mesures
                        WHERE {where}
                        GROUP BY {groupby}
                        ORDER BY {orderby}""".format(indicator = indicator, where = where, groupby = groupby, orderby = orderby))
        rows = cursor.fetchall()
    return rows

# Fonction pour créer une requete SQL
def getIndicator2(indicator, where, groupby, orderby):
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute("""SELECT {groupby}, {indicator} FROM mesures
                        WHERE {where}
                        GROUP BY {groupby}
                        ORDER BY {orderby}""".format(indicator = indicator, where = where, groupby = groupby, orderby = orderby))
        rows = cursor.fetchall()
    return rows

def remplacer_valeurs(indicateur, ind_target, group1, group2, order1, order2):
    match indicateur:
        case 'Aucun':
            indicateur = '0'
        case 'Moyenne':
            indicateur = 'AVG'
        case 'Minimum':
            indicateur = 'MIN'
        case 'Maximum':
            indicateur = 'MAX'
        case 'Compte':
            indicateur = 'COUNT'
    ind_target = request.form['val_indicateur']
    match ind_target:
        case 'Valeur 1':
            ind_target = 'val1'
        case 'Valeur 2':   
            ind_target = 'val2'
        case 'Valeur 3':
            ind_target = 'val3'
    Indicateur = f'{indicateur}({ind_target})'
    #groupby
    group1 = request.form['group1']
    group2 = request.form['group2']
    match group1:
        case 'Aucun':
            group1 = '0'
        case 'Année':
            group1 = 'year'
        case 'Mois':
            group1 = 'month'
        case 'Jour':
            group1 = 'day'
        case 'Type':    
            group1 = 'type'

    match group2:
        case 'Aucun':
            group2 = ''
        case 'Année':
            group2 = 'year'
        case 'Mois':
            group2 = 'month'
        case 'Jour':
            group2 = 'day'
        case 'Type':    
            group2 = 'type'
    if group2 == '':
        groupby = group1
    else: groupby = f'{group1}, {group2}'


    #orderby
    order1 = request.form['order1']
    order2 = request.form['order2']
    match order1:
        case 'Aucun':
            order1 = '0'
        case 'Année':
            order1 = 'year'
        case 'Mois':
            order1 = 'month'
        case 'Jour':
            order1 = 'day'
        case 'Type':    
            order1 = 'type'
        case 'Valeur 1':
            order1 = 'val1'
        case 'Valeur 2':    
            order1 = 'val2'
        case 'Valeur 3':
            order1 = 'val3'
    match order2:
        case 'Aucun':
            order2 = ''
        case 'Année':
            order2 = 'year'
        case 'Mois':
            order2 = 'month'
        case 'Jour':
            order2 = 'day'
        case 'Type':    
            order2 = 'type'
        case 'Valeur 1':
            order2 = 'val1'
        case 'Valeur 2':    
            order2 = 'val2'
        case 'Valeur 3':
            order2 = 'val3'
    if order2 == '':
        orderby = order1
    else : orderby = f'{order1}, {order2}'
    return Indicateur, group1, group2, groupby, orderby


### Initialiser Faker avec la localisation canada francais ###
fake = Faker(['fr_CA'])

### Initialiser la base de données ###
initdb()


### APP ###
# on crée l'application
app = Flask(__name__)

# Route GET : Afficher la page d'accueil
@app.route('/')
def home():
    return render_template('index.html')

# Route GET : Afficher toutes les mesures
@app.route('/mesures')
def pageMesures():
    # on cherche tous les points
    rows = getAllPoints()
    # on affiche la page d'accueil
    return render_template('mesures.html', points=rows)

# Route POST : Afficher les mesures autour d'un point
@app.route('/mesures/near' , methods=['GET', 'POST'])
def pageMesuresNear():
    # Récupérer les paramètres de la requête et convertir
    position = request.form['position']
    position = position.split(",")
    position = [float(position[0]), float(position[1])]
    distance = request.form['distance']
    distance = float(distance)
    
    # Récupérer les points
    rows = getPointsRange(position, distance)

    return render_template('mesures.html', points=rows)

# Route POST : Afficher les données pour un indicateur
@app.route('/mesures/filtered' , methods=['GET', 'POST'])
#Intervalle
def MesuresIndicateur():
    start = request.form['date1']
    end = request.form['date2']
    intervalle = 'date BETWEEN "' + start + '" AND "' + end + '"'
    #Indicateur
    indicateur = request.form['indicateur']
    ind_target = request.form['val_indicateur']
    #groupby
    groupA = request.form['group1']
    groupB = request.form['group2']
    #orderby
    order1 = request.form['order1']
    order2 = request.form['order2']
    #remplacer les valeurs
    indicateur_choisi, group1, group2, groupby, orderby = remplacer_valeurs(indicateur, ind_target, groupA, groupB, order1, order2)

    rows = getIndicator2(indicateur_choisi, intervalle, groupby, orderby)

    # return render_template('mesures.html', points=rows)
    return render_template_string(
        """
            {% extends "mesures.html" %}
            {% block header %}
            
            <th>{{ Groupby1|safe }}</th>
            <th>{{ Groupby2|safe }}</th>
            <th>{{ Indicateur|safe }}</th>

            {% endblock header %}""",
            points = rows,
            Indicateur = indicateur,
            Groupby1 = groupA,
            Groupby2 = groupB)


# Route GET : Afficher une carte présentant toutes les mesures
@app.route("/map")
def map():
    """Embed a map as an iframe on a page."""
    m = folium.Map(location= (latSh, lonSh), zoom_start=12)
    m.add_child(folium.ClickForLatLng(format_str='lat + "," + lng', alert=False))
    rows = getAllPoints()
    dfrows = pd.DataFrame(rows, columns = ['id','lat', 'lon', 'date','year', 'month', 'day', 'type', 'val1', 'val2', 'val3'])
    MarkerCluster(locations = dfrows[['lat', 'lon']]).add_to(m)

    # set the iframe width and height
    m.get_root().width = "800px"
    m.get_root().height = "600px"
    iframe = m.get_root()._repr_html_()

    return render_template_string(
        """
            {% extends "map.html" %}

            {% block map %}
                    {{ iframe|safe }}
                    </div>
            {% endblock %}       """,
        iframe=iframe, points = rows,
    )

# Route POST : Afficher une carte présentant seulement les mesures à l'intérieur d'un radius autour de lat/lon
@app.route("/map/near", methods=['GET', 'POST'])
def near():
    # Récupérer les paramètres de la requête et convertir
    position = request.form['position']
    position = position.split(",")
    position = [float(position[0]), float(position[1])]
    distance = request.form['distance']
    distance = float(distance)
    """Embed a map as an iframe on a page."""

    # Créer carte
    m = folium.Map(location=position, zoom_start=12)
    m.add_child(folium.ClickForLatLng(format_str='lat + "," + lng', alert=False))

    # Récupérer les points
    rows = getPointsRange(position, distance)
    dfrows = pd.DataFrame(rows, columns = ['id','lat', 'lon', 'date','year', 'month', 'day', 'type', 'val1', 'val2', 'val3'])

    # Créer marqueurs et ajouter à la carte
    MarkerCluster(locations = dfrows[['lat', 'lon']]).add_to(m)

    #Création d'un cercle représentant l'aire filtrée
    radius = distance
    folium.Circle(
        location=position,
        radius=distance,
        color="black",
        weight=1,
        fill_opacity=0.6,
        opacity=1,
        fill_color="red",
        fill=False,  # gets overridden by fill_color
        popup="{} meters".format(radius),
        tooltip="I am in meters",
    ).add_to(m)

    # set the iframe width and height
    m.get_root().width = "800px"
    m.get_root().height = "600px"
    iframe = m.get_root()._repr_html_()
    

    return render_template_string(
        """
            {% extends "map.html" %}

            {% block map %}
                    {{ iframe|safe }}
                </div>
            {% endblock %} """,
        iframe=iframe,
        points = rows
    )




# Route GET : Afficher un heatmap de toutes les mesures
@app.route("/heatmap")
def heatmap():
    """Embed a map as an iframe on a page."""
    m = folium.Map(location= (latSh, lonSh), zoom_start=11)
    # Récupérer les points
    rows = getAllPoints()
    # transformer en dataframe
    dfrows = pd.DataFrame(rows, columns = ['id','lat', 'lon', 'date','year', 'month', 'day', 'type', 'val1', 'val2', 'val3'])
    df_heatmap = dfrows[['lat', 'lon', 'val2']]
    HeatMap(df_heatmap, radius = 17).add_to(m)

    # Créer iframe pour la carte
    m.get_root().width = "800px"
    m.get_root().height = "600px"
    iframe = m.get_root()._repr_html_()

    return render_template_string(
        """
            {% extends "map.html" %}
            {% block form %}
            {% endblock %} 


            {% block map %}
                    {{ iframe|safe }}
                    </div>
            {% endblock %}       """,
        iframe=iframe, points = rows,
    )

# Route GET : Afficher un heatmap de toutes les mesures
@app.route("/time_heatmap")
def heatmap_time():
    """Embed a map as an iframe on a page."""
    m = folium.Map(location= (latSh, lonSh), zoom_start=11)
    rows = getAllPoints()
    dfrows = pd.DataFrame(rows, columns = ['id','lat', 'lon', 'date','year', 'month', 'day', 'type', 'val1', 'val2', 'val3'])
    # Enlever les jours pour avoir les données par mois seulement
    dfrows['date'] = dfrows['date'].str[:-3]
    #Créer un index temporel pour le heatmap
    time_index = list(dfrows['date'].sort_values().astype('str').unique())
    dfrows['date'] = dfrows['date'].sort_values(ascending=True)
    data = []
    for _, d in dfrows.groupby('date'):
        data.append([[row['lat'], row['lon'], row['val2']] for _, row in d.iterrows()])
    # Créer heatmap temporel
    HeatMapWithTime(data,
                index=time_index,
                auto_play=True,
                radius = 50,
                use_local_extrema=True
               ).add_to(m)

    # iframe pour la carte
    m.get_root().width = "800px"
    m.get_root().height = "600px"
    iframe = m.get_root()._repr_html_()

    return render_template_string(
        """
            {% extends "map.html" %}
            {% block form %}
            {% endblock %} 


            {% block map %}
                    {{ iframe|safe }}
                    </div>
            {% endblock %}       """,
        iframe=iframe, points=rows,
    )

# Route GET : Afficher un graphique avec plotly
@app.route('/graph')
def graph():
    
    rows = getIndicator('COUNT(val2)', 'year > 2019', 'year, type', 'year, month ASC')
    df_rows = pd.DataFrame(rows, columns = ['id', 'year', 'month', 'day', 'type', 'Nb de mesures'])

    fig = px.bar(df_rows, x="type", y="Nb de mesures", color="year", title="Number of measurements per year and type of measurement")

    graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

    return render_template('graph.html', graphJSON=graphJSON)

# Route GET : Afficher un graphique pie chart avec plotly
@app.route('/pie')
def pie():
    
    rows = getIndicator('COUNT(val2)', 'year > 2019', 'year, type', 'year, month ASC')
    df_rows = pd.DataFrame(rows, columns = ['id', 'year', 'month', 'day', 'type', 'Nb de mesures'])

    fig = px.pie(df_rows, values="Nb de mesures", names="type", title="Pie Chart")

    graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

    return render_template('graph.html', graphJSON=graphJSON)


# on lance l'application
if __name__ == '__main__':
    app.run(debug=False)

