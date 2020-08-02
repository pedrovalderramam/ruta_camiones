
import os
from flask import Flask, render_template, request, redirect, url_for, send_from_directory
from werkzeug.utils import secure_filename
import AgenteViajero
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp
from bikeroute import Map, Route

app = Flask(__name__)

app.config['UPLOAD_FOLDER'] = 'static\Datos'
app.config['ALLOWED_EXTENSIONS'] = set(['txt'])
app.config['API_KEY'] = "AIzaSyBuwdmW9ea9zVsAYsUb7U9Ere1h9mHbhIQ"


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in app.config['ALLOWED_EXTENSIONS']


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
def upload():
    archivos_cargados = request.files.getlist("files[]")
    centro = int(request.form.get('centro'))
    productos = int(request.form.get('productos'))
    filenames = []
    print("Archivos cargados",archivos_cargados)
    for file in archivos_cargados:
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            filenames.append(filename)

    ###############################################################################################
    # Creacion de las estructuras a utilizar
    datos = {}
    datos_centros = []
    datos_nombres = list()
    ruta = list()
    rutaCoord = dict()


    if productos <= 1000:

        # Interpretacion del archivo
        datosArchivo = open('static/Datos/parametros.txt', mode='r', encoding='utf-8')
        datos_lineas = datosArchivo.readlines()
        for linea in datos_lineas:
            separado = linea.split(';')
            if separado[0] == 'P':
                x = int(separado[2].split(',')[0])
                y = int(separado[2].split(',')[1])
                datos_centros.append((x, y))
                datos_nombres.append(separado[1])
                rutaCoord.update({separado[1]: (x, y)})
            if separado[0] == 'C' and int(separado[1]) == centro:
                x = int(separado[2].split(',')[0])
                y = int(separado[2].split(',')[1])
                primero = (x, y)
                datos_centros.insert(0, primero)
                datos_nombres.insert(0, separado[1])
                rutaCoord.update({separado[1]: primero})
        datos['centros'] = datos_centros
        datos['num_vehicles'] = 1
        datos['depot'] = 0
        manager = pywrapcp.RoutingIndexManager(len(datos['centros']), datos['num_vehicles'], datos['depot'])
        routing = pywrapcp.RoutingModel(manager)
        distance_matrix = AgenteViajero.compute_euclidean_distance_matrix(datos['centros'])

        def distance_callback(from_index, to_index):
            from_node = manager.IndexToNode(from_index)
            to_node = manager.IndexToNode(to_index)
            return distance_matrix[from_node][to_node]

        transit_callback_index = routing.RegisterTransitCallback(distance_callback)

        routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

        search_parameters = pywrapcp.DefaultRoutingSearchParameters()
        search_parameters.first_solution_strategy = (
            routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC)

        solution = routing.SolveWithParameters(search_parameters)
        if solution:
            print('Objetivo: {}'.format(solution.ObjectiveValue()) + ' Km')
            index = routing.Start(0)
            plan_output = 'Ruta:\n'
            route_distance = 0
            while not routing.IsEnd(index):
                plan_output += ' {} ->'.format(datos_nombres[manager.IndexToNode(index)])
                ruta.append(datos_nombres[manager.IndexToNode(index)])
                previous_index = index
                index = solution.Value(routing.NextVar(index))
                route_distance += routing.GetArcCostForVehicle(previous_index, index, 0)
            plan_output += ' {}\n'.format(datos_nombres[manager.IndexToNode(index)])
            ruta.append(datos_nombres[manager.IndexToNode(index)])
            plan_output += 'Objetivo: {}m\n'.format(route_distance)
            AgenteViajero.CrearXML(ruta, rutaCoord)
            print(plan_output)
            print(ruta)
            rutaA = open("static/Datos/ruta.txt", "w")
            print("\n\nLa ruta del dia es la siguiente:\n\n", file=rutaA)
            for dato in ruta:
                print("Locacion:" + dato, file=rutaA)
    else:
        rutaA = open("static/Datos/ruta.txt", "w")
        print("El camion no puede llevar mas de 1000 mercancias", file=rutaA)
    ###########################################################################################################33
    route = Route("static/Datos/ruta.xml")
    map = Map(route.trackpoints)
    context = {
        "key": app.config['API_KEY'],
        "title": route.title
    }
    return render_template('upload.html', filenames=filenames,map=map, context=context)

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'],
                               filename)
@app.route('/descargar')
def downloaded_file():
    return send_from_directory(app.config['UPLOAD_FOLDER'],
                               'ruta.txt')

if __name__ == '__main__':
    app.run(
        host="127.0.0.1",
        port=int("80"),
        debug=True
    )
