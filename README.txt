Pour accéder à l'API, ouvrir l'application avec un éditeur python et exécuter le code
après avoir installer toutes les librairies dans le fichier requirements.txt
et entrer l'adresse http://127.0.0.1:5000 dans votre fureteur. Il est conseillé de spécifier
la localisation désirée pour la base de données fictive créée.

L'application permet de faire quelques manipulations sur des données fictives.

/mesures : Affiche toutes les mesures dans un tableau

/mesures/near : Affiche dans un tableau toutes les mesures dans un radius déterminé par l'utilisateur autour d'un point
(latitude/longitude) également déterminé par l'utilisateur. Fonctionnel via un formulaire à partir de /mesures

/mesures/filtered : Affiche dans un tableau l'indicateur choisi par l'utilisateur pour une période donnée. 
Fonctionnel via un formulaire à partir de /mesures

/map : affiche une carte avec tous les points, en "clusters"

/map/near : affiche une carte avec uniquement les données autour d'un point sélectionné, dans un radius sélectionné.

/heatmap : affiche une carte de chaleur de tous les points

/time_heatmap : affiche une carte de chaleur temporelle, regroupant les valeurs par mois.

/graph : affiche un graphique en barre simple regroupement le total des données par type.

/pie : affiche un diagramme circulaire (pie chart) regroupement les données par type.