#!/usr/bin/python2.5
#
# Copyright 2009 Roman Nurik
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Defines the notion of 'geocells' and exposes methods to operate on them.

A geocell is a hexadecimal string that defines a two dimensional rectangular
region inside the [-90,90] x [-180,180] latitude/longitude space. A geocell's
'resolution' is its length. For most practical purposes, at high resolutions,
geocells can be treated as single points.

Much like geohashes (see http://en.wikipedia.org/wiki/Geohash), geocells are
hierarchical, in that any prefix of a geocell is considered its ancestor, with
geocell[:-1] being geocell's immediate parent cell.

To calculate the rectangle of a given geocell string, first divide the
[-90,90] x [-180,180] latitude/longitude space evenly into a 4x4 grid like so:

             +---+---+---+---+ (90, 180)
             | a | b | e | f |
             +---+---+---+---+
             | 8 | 9 | c | d |
             +---+---+---+---+
             | 2 | 3 | 6 | 7 |
             +---+---+---+---+
             | 0 | 1 | 4 | 5 |
  (-90,-180) +---+---+---+---+

NOTE: The point (0, 0) is at the intersection of grid cells 3, 6, 9 and c. And,
      for example, cell 7 should be the sub-rectangle from
      (-45, 90) to (0, 180).

Calculate the sub-rectangle for the first character of the geocell string and
re-divide this sub-rectangle into another 4x4 grid. For example, if the geocell
string is '78a', we will re-divide the sub-rectangle like so:

               .                   .
               .                   .
           . . +----+----+----+----+ (0, 180)
               | 7a | 7b | 7e | 7f |
               +----+----+----+----+
               | 78 | 79 | 7c | 7d |
               +----+----+----+----+
               | 72 | 73 | 76 | 77 |
               +----+----+----+----+
               | 70 | 71 | 74 | 75 |
  . . (-45,90) +----+----+----+----+
               .                   .
               .                   .

Continue to re-divide into sub-rectangles and 4x4 grids until the entire
geocell string has been exhausted. The final sub-rectangle is the rectangular
region for the geocell.
"""

__author__ = 'api.roman.public@gmail.com (Roman Nurik)'

import os.path
import sys

import geomath
import geotypes
from math import log,ceil
import logging

# Geocell algorithm constants.
_GEOCELL_GRID_SIZE = 2
_GEOCELL_ALPHABET = '0123'

# The maximum *practical* geocell resolution.
MAX_GEOCELL_RESOLUTION = 14

# The maximum number of geocells to consider for a bounding box search.
MAX_FEASIBLE_BBOX_SEARCH_CELLS = 300

# Direction enumerations.
NORTHWEST = (-1, 1)
NORTH = (0, 1)
NORTHEAST = (1, 1)
EAST = (1, 0)
SOUTHEAST = (1, -1)
SOUTH = (0, -1)
SOUTHWEST = (-1, -1)
WEST = (-1, 0)


def best_bbox_search_cells(bbox, cost_function):
  """Returns an efficient set of geocells to search in a bounding box query.

  This method is guaranteed to return a set of geocells having the same
  resolution.

  Args:
    bbox: A geotypes.Box indicating the bounding box being searched.
    cost_function: A function that accepts two arguments:
        * num_cells: the number of cells to search
        * resolution: the resolution of each cell to search
        and returns the 'cost' of querying against this number of cells
        at the given resolution.

  Returns:
    A list of geocell strings that contain the given box.
  """
  cell_ne = compute(bbox.north_east, resolution=MAX_GEOCELL_RESOLUTION)
  cell_sw = compute(bbox.south_west, resolution=MAX_GEOCELL_RESOLUTION)

  
  
  # The current lowest BBOX-search cost found; start with practical infinity.
  min_cost = 1e10000

  # The set of cells having the lowest calculated BBOX-search cost.
  min_cost_cell_set = None

  # First find the common prefix, if there is one.. this will be the base
  # resolution.. i.e. we don't have to look at any higher resolution cells.\
  common_prefix = os.path.commonprefix([cell_sw, cell_ne])
  min_resolution = len(common_prefix)

  
  #ancho del viewport
  vpw = bbox.north_east.lon - bbox.south_west.lon
  deep=1
  if vpw > 0:
    xx  = log(360.0/vpw)
    if xx > 0:
      deep = int(ceil(xx/log(_GEOCELL_GRID_SIZE)))-1
  
  if deep > MAX_GEOCELL_RESOLUTION:
    deep = MAX_GEOCELL_RESOLUTION
  logging.debug('best_bbox_search_cells() deep:[%s]; cell_sw:[%s]; cell_ne:[%s]; common_prefix:[%s]; min_resolution:[%s]; MAX_GEOCELL_RESOLUTION[%s]' % (str(deep), cell_sw, cell_ne, common_prefix,  str(min_resolution), str(MAX_GEOCELL_RESOLUTION)))
  
  if min_resolution == deep or deep<6:
    logging.debug(' (if min_resolution == deep or deep<6:) ES VERDADERO!!!')
    return common_prefix, str(compute_box(common_prefix))
  
  #buscamos un primo sobre min_resolution (la caja grande)
  p0 = geotypes.Point(bbox.north_east.lat, bbox.south_west.lon)
  
  p0cell_gorda = compute(p0, MAX_GEOCELL_RESOLUTION, False)
  
  new_deep=deep
  
  p0cell = p0cell_gorda[:new_deep]
  
  p0New = compute_box(p0cell) 
  
  dx = 360.0/pow(_GEOCELL_GRID_SIZE,new_deep)/4.0
  dy = 180.0/pow(_GEOCELL_GRID_SIZE,new_deep)/4.0
  
  primo_prefix = '0'
  primo_width = 4.0
  if vpw> (3*dx):
    primo_prefix = '1'
    primo_width = 5.0
    
  #dx    => 1 de los chiquitos (deep+1)
  #dy    => 1 de los chiquitos (deep+1)
  #p0    => view port (top,left)
  #p0New => Box del gordo (deep-1)
  
  primoX0 = abs(int((p0.lon - p0New.south_west.lon)/dx))
  primoY0 = abs(int((p0.lat - p0New.north_east.lat)/dy))

  boxprimo = geotypes.Box(p0New.north_east.lat-(dy*primoY0),
                          p0New.south_west.lon+(dx*primoX0)+(dx*primo_width),
                          p0New.north_east.lat-(dy*primoY0)-(dy*primo_width),
                          p0New.south_west.lon+(dx*primoX0))
  
  the_primo = p0cell + '.' + primo_prefix+ str(primoX0)+str(primoY0)

  #logging.error('SIEMPRE ENCUENTRO EL PRIMO %s' % the_primo)

  return the_primo , boxprimo
    
def collinear(cell1, cell2, column_test):
  """Determines whether the given cells are collinear along a dimension.

  Returns True if the given cells are in the same row (column_test=False)
  or in the same column (column_test=True).

  Args:
    cell1: The first geocell string.
    cell2: The second geocell string.
    column_test: A boolean, where False invokes a row collinearity test
        and 1 invokes a column collinearity test.

  Returns:
    A bool indicating whether or not the given cells are collinear in the given
    dimension.
  """
  for i in range(min(len(cell1), len(cell2))):
    x1, y1 = _subdiv_xy(cell1[i])
    x2, y2 = _subdiv_xy(cell2[i])

    # Check row collinearity (assure y's are always the same).
    if not column_test and y1 != y2:
      return False

    # Check column collinearity (assure x's are always the same).
    if column_test and x1 != x2:
      return False

  return True


def interpolate(cell_ne, cell_sw):
  """Calculates the grid of cells formed between the two given cells.

  Generates the set of cells in the grid created by interpolating from the
  given Northeast geocell to the given Southwest geocell.

  Assumes the Northeast geocell is actually Northeast of Southwest geocell.

  Arguments:
    cell_ne: The Northeast geocell string.
    cell_sw: The Southwest geocell string.

  Returns:
    A list of geocell strings in the interpolation.
  """
  # 2D array, will later be flattened.
  cell_set = [[cell_sw]]

  # First get adjacent geocells across until Southeast--collinearity with
  # Northeast in vertical direction (0) means we're at Southeast.
  while not collinear(cell_set[0][-1], cell_ne, True):
    cell_tmp = adjacent(cell_set[0][-1], (1, 0))
    if cell_tmp is None:
      break
    cell_set[0].append(cell_tmp)

  # Then get adjacent geocells upwards.
  while cell_set[-1][-1] != cell_ne:
    cell_tmp_row = [adjacent(g, (0, 1)) for g in cell_set[-1]]
    if cell_tmp_row[0] is None:
      break
    cell_set.append(cell_tmp_row)

  # Flatten cell_set, since it's currently a 2D array.
  return [g for inner in cell_set for g in inner]


def interpolation_count(cell_ne, cell_sw):
  """Computes the number of cells in the grid formed between two given cells.

  Computes the number of cells in the grid created by interpolating from the
  given Northeast geocell to the given Southwest geocell. Assumes the Northeast
  geocell is actually Northeast of Southwest geocell.

  Arguments:
    cell_ne: The Northeast geocell string.
    cell_sw: The Southwest geocell string.

  Returns:
    An int, indicating the number of geocells in the interpolation.
  """
  bbox_ne = compute_box(cell_ne)
  bbox_sw = compute_box(cell_sw)

  cell_lat_span = bbox_sw.north - bbox_sw.south
  cell_lon_span = bbox_sw.east - bbox_sw.west

  num_cols = int((bbox_ne.east - bbox_sw.west) / cell_lon_span)
  num_rows = int((bbox_ne.north - bbox_sw.south) / cell_lat_span)

  return num_cols * num_rows


def all_adjacents(cell):
  """Calculates all of the given geocell's adjacent geocells.

  Args:
    cell: The geocell string for which to calculate adjacent/neighboring cells.

  Returns:
    A list of 8 geocell strings and/or None values indicating adjacent cells.
  """
  return [adjacent(cell, d) for d in [NORTHWEST, NORTH, NORTHEAST, EAST,
                                      SOUTHEAST, SOUTH, SOUTHWEST, WEST]]


def adjacent(cell, dir):
  """Calculates the geocell adjacent to the given cell in the given direction.

  Args:
    cell: The geocell string whose neighbor is being calculated.
    dir: An (x, y) tuple indicating direction, where x and y can be -1, 0, or 1.
        -1 corresponds to West for x and South for y, and
         1 corresponds to East for x and North for y.
        Available helper constants are NORTH, EAST, SOUTH, WEST,
        NORTHEAST, NORTHWEST, SOUTHEAST, and SOUTHWEST.

  Returns:
    The geocell adjacent to the given cell in the given direction, or None if
    there is no such cell.
  """
  if cell is None:
    return None

  dx = dir[0]
  dy = dir[1]

  cell_adj_arr = list(cell)  # Split the geocell string characters into a list.
  i = len(cell_adj_arr) - 1

  while i >= 0 and (dx != 0 or dy != 0):
    x, y = _subdiv_xy(cell_adj_arr[i])

    # Horizontal adjacency.
    if dx == -1:  # Asking for left.
      if x == 0:  # At left of parent cell.
        x = _GEOCELL_GRID_SIZE - 1  # Becomes right edge of adjacent parent.
      else:
        x -= 1  # Adjacent, same parent.
        dx = 0  # Done with x.
    elif dx == 1:  # Asking for right.
      if x == _GEOCELL_GRID_SIZE - 1:  # At right of parent cell.
        x = 0  # Becomes left edge of adjacent parent.
      else:
        x += 1  # Adjacent, same parent.
        dx = 0  # Done with x.

    # Vertical adjacency.
    if dy == 1:  # Asking for above.
      if y == _GEOCELL_GRID_SIZE - 1:  # At top of parent cell.
        y = 0  # Becomes bottom edge of adjacent parent.
      else:
        y += 1  # Adjacent, same parent.
        dy = 0  # Done with y.
    elif dy == -1:  # Asking for below.
      if y == 0:  # At bottom of parent cell.
        y = _GEOCELL_GRID_SIZE - 1  # Becomes top edge of adjacent parent.
      else:
        y -= 1  # Adjacent, same parent.
        dy = 0  # Done with y.

    cell_adj_arr[i] = _subdiv_char((x,y))
    i -= 1

  # If we're not done with y then it's trying to wrap vertically,
  # which is a failure.
  if dy != 0:
    return None

  # At this point, horizontal wrapping is done inherently.
  return ''.join(cell_adj_arr)


def contains_point(cell, point):
  """Returns whether or not the given cell contains the given point."""
  return compute(point, len(cell)) == cell


def point_distance(cell, point):
  """Returns the shortest distance between a point and a geocell bounding box.

  If the point is inside the cell, the shortest distance is always to a 'edge'
  of the cell rectangle. If the point is outside the cell, the shortest distance
  will be to either a 'edge' or 'corner' of the cell rectangle.

  Returns:
    The shortest distance from the point to the geocell's rectangle, in meters.
  """
  bbox = compute_box(cell)

  between_w_e = bbox.west <= point.lon and point.lon <= bbox.east
  between_n_s = bbox.south <= point.lat and point.lat <= bbox.north

  if between_w_e:
    if between_n_s:
      # Inside the geocell.
      return min(geomath.distance(point, (bbox.south, point.lon)),
                 geomath.distance(point, (bbox.north, point.lon)),
                 geomath.distance(point, (point.lat, bbox.east)),
                 geomath.distance(point, (point.lat, bbox.west)))
    else:
      return min(geomath.distance(point, (bbox.south, point.lon)),
                 geomath.distance(point, (bbox.north, point.lon)))
  else:
    if between_n_s:
      return min(geomath.distance(point, (point.lat, bbox.east)),
                 geomath.distance(point, (point.lat, bbox.west)))
    else:
      # TODO(romannurik): optimize
      return min(geomath.distance(point, (bbox.south, bbox.east)),
                 geomath.distance(point, (bbox.north, bbox.east)),
                 geomath.distance(point, (bbox.south, bbox.west)),
                 geomath.distance(point, (bbox.north, bbox.west)))


def compute(point, resolution=MAX_GEOCELL_RESOLUTION, get_primos=False):
  """Computes the geocell containing the given point to the given resolution.

  This is a simple 16-tree lookup to an arbitrary depth (resolution).

  Args:
    point: The geotypes.Point to compute the cell for.
    resolution: An int indicating the resolution of the cell to compute.

  Returns:
    The geocell string containing the given point, of length <resolution>.
  """
  north = 90.0
  south = -90.0
  east = 180.0
  west = -180.0

  primos = []
  cell = ''
  #print 'point: '+str(point)
  while len(cell) < resolution:
    subcell_lon_span = (east - west) / _GEOCELL_GRID_SIZE
    subcell_lat_span = (north - south) / _GEOCELL_GRID_SIZE

    x = min(int(_GEOCELL_GRID_SIZE * (point.lon - west) / (east - west)),
            _GEOCELL_GRID_SIZE - 1)
    y = min(int(_GEOCELL_GRID_SIZE * (point.lat - south) / (north - south)),
            _GEOCELL_GRID_SIZE - 1)

    cell += _subdiv_char((x,y))
    
    if get_primos and len(cell)>4:
      #ancho del level dividido 4
      dx = subcell_lon_span/4
      dy = subcell_lat_span/4
      
      #celdas: 0 es en la que estamos, tenemos que probar en 1 y 2 
      #     [2]
      #  [1][0]
      cells = [cell,
               adjacent(cell, (-1,0)),
               adjacent(cell, (0,1)),
               adjacent(cell, (-1,1))]
               
      # cell: The geocell string whose neighbor is being calculated.
      # dir: An (x, y) tuple indicating direction, where x and y can be -1, 0, or 1.
      #   -1 corresponds to West for x and South for y, and
      #   1 corresponds to East for x and North for y.
      
      # boxes=[]
      #print '    dx (dLon): '+str(dx)
      #print '    dy (dLat): '+str(dy)
            
      #iteramos longitud
      for k in range(len(cells)):
        cur_cell = cells[k]
        
        #Skipeamos si es la misma (caso borde del mundo)
        if cur_cell == cell and k > 0:
          continue
        
        #Calculamos la caja de la celda actual        
        box = compute_box(cur_cell)

        #Armamos el punto superior-izquierdo
        p0 = geotypes.Point(box.north_east.lat, box.south_west.lon)
        
        # print ' width: '+str(box.north_east.lon-box.south_west.lon)
        # print 'box: '+str(box)
        # print 'box point: '+str(p0)
        
        for xx in [0, 1]:
          for i in range(0,4):
            for j in range(0,4):
              if xx==0 and i==0 and j==0:
                continue
              bbox = geotypes.Box(box.north_east.lat-(dy*j)
                      , box.north_east.lon+(dx*i)+(dx*xx)
                      , box.south_west.lat-(dy*j)-(dy*xx)
                      , box.south_west.lon+(dx*i))
              # bbox = geotypes.Box(  p0.lat-(dy*j)         # north
                                  # , p0.lon+(dy*j)+(dy*xx) # east
                                  # , p0.lat-(dx*i)-(dx*xx) # south
                                  # , p0.lon+(dx*i)         # west
                                # )
              # print '    '+cur_cell +'.'+str(xx) +str(i)+str(j)+str(bbox)
              # print cur_cell +'.'+str(xx) +str(i)+str(j) + '|-|'+str(box)+'-'+str(bbox)

              if is_in_box(bbox, point):
                the_cell = cur_cell +'.'+str(xx) +str(i)+str(j)
                primos.append(the_cell)
                # boxes.append(bbox)
        
        # print 'k:'+str(k)+'  boxes:'+ str(map(lambda x:str(x),boxes))
        # boxes=[]
      # exit(0)
    south += subcell_lat_span * y
    north = south + subcell_lat_span

    west += subcell_lon_span * x
    east = west + subcell_lon_span
    
  if get_primos:
    return (cell, primos)
  
  return cell

def is_in_box(box, point):
  """Returns whether or not the given box contains the given point."""
  if (  point.lat <= box.north_east.lat and
        point.lat >= box.south_west.lat and
        point.lon >= box.south_west.lon and
        point.lon <= box.north_east.lon ):
    return True
  return False
  
def compute_box(cell):
  """Computes the rectangular boundaries (bounding box) of the given geocell.

  Args:
    cell: The geocell string whose boundaries are to be computed.

  Returns:
    A geotypes.Box corresponding to the rectangular boundaries of the geocell.
  """
  if cell is None:
    return None

  bbox = geotypes.Box(90.0, 180.0, -90.0, -180.0)

  while len(cell) > 0:
    subcell_lon_span = (bbox.east - bbox.west) / _GEOCELL_GRID_SIZE
    subcell_lat_span = (bbox.north - bbox.south) / _GEOCELL_GRID_SIZE

    x, y = _subdiv_xy(cell[0])

    bbox = geotypes.Box(bbox.south + subcell_lat_span * (y + 1),
                        bbox.west  + subcell_lon_span * (x + 1),
                        bbox.south + subcell_lat_span * y,
                        bbox.west  + subcell_lon_span * x)

    cell = cell[1:]

  return bbox


def is_valid(cell):
  """Returns whether or not the given geocell string defines a valid geocell."""
  return bool(cell and reduce(lambda val, c: val and c in _GEOCELL_ALPHABET,
                              cell, True))


def children(cell):
  """Calculates the immediate children of the given geocell.

  For example, the immediate children of 'a' are 'a0', 'a1', ..., 'af'.
  """
  return [cell + chr for chr in _GEOCELL_ALPHABET]


def _subdiv_xy(char):
  """Returns the (x, y) of the geocell character in the 4x4 alphabet grid."""
  # NOTE: This only works for grid size 4.
  pos = _GEOCELL_ALPHABET.index(char)
  
  y = int(pos/_GEOCELL_GRID_SIZE)
  x = pos - y*_GEOCELL_GRID_SIZE
  return (x,y)
  
  char = _GEOCELL_ALPHABET.index(char)
  return ((char & 4) >> 1 | (char & 1) >> 0,
          (char & 8) >> 2 | (char & 2) >> 1)


def _subdiv_char(pos):
  """Returns the geocell character in the 4x4 alphabet grid at pos. (x, y)."""
  return str(pos[1]*_GEOCELL_GRID_SIZE+pos[0])
  # NOTE: This only works for grid size 4.
  return _GEOCELL_ALPHABET[
      (pos[1] & 2) << 2 |
      (pos[0] & 2) << 1 |
      (pos[1] & 1) << 1 |
      (pos[0] & 1) << 0]
