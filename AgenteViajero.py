import math
import xml.etree.ElementTree as ET
from datetime import datetime


def compute_euclidean_distance_matrix(locations):
    """Creates callback to return distance between points."""
    distances = {}
    for from_counter, from_node in enumerate(locations):
        distances[from_counter] = {}
        for to_counter, to_node in enumerate(locations):
            if from_counter == to_counter:
                distances[from_counter][to_counter] = 0
            else:
                # Euclidean distance
                distances[from_counter][to_counter] = (int(
                    math.hypot((from_node[0] - to_node[0]),
                               (from_node[1] - to_node[1]))))
    return distances


def print_solution(manager, routing, solution):
    """Prints solution on console."""
    print('Objective: {}'.format(solution.ObjectiveValue()))
    index = routing.Start(0)
    plan_output = 'Route:\n'
    route_distance = 0
    while not routing.IsEnd(index):
        plan_output += ' {} ->'.format(manager.IndexToNode(index))
        previous_index = index
        index = solution.Value(routing.NextVar(index))
        route_distance += routing.GetArcCostForVehicle(previous_index, index, 0)
    plan_output += ' {}\n'.format(manager.IndexToNode(index))
    print(plan_output)
    plan_output += 'Objective: {}m\n'.format(route_distance)

def CrearXML(ruta,rutaCoord):
    track = ET.Element('track')
    for r in ruta:

        trackpoint = ET.SubElement(track, 'Trackpoint')
        time = ET.SubElement(trackpoint, 'Time')
        position = ET.SubElement(trackpoint, 'Position')
        distancemeters = ET.SubElement(trackpoint, 'DistanceMeters')

        lon = ET.SubElement(position, 'LongitudeDegrees')
        lat = ET.SubElement(position, 'LatitudeDegrees')
        lon.text = str(rutaCoord[r][0])
        lat.text = str(rutaCoord[r][1])
        time.text = str(datetime.now())
        distancemeters.text = '0.0000'

    # create a new XML file with the results
    mydata = ET.tostring(track)
    myfile = open("static/Datos/ruta.xml", "w")
    myfile.write(mydata.decode())
