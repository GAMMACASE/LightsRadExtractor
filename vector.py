"""
https://gist.github.com/mcleonard/5351452
The MIT License (MIT)

Copyright (c) 2015 Mat Leonard

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
"""

import math


class Vector(object):
	def __init__(self, *args):
		""" Create a vector, example: v = Vector(1,2,3) """
		if len(args) == 0:
			self.values = [0, 0, 0]
		else:
			self.values = list(args)

	def length(self):
		""" Returns the length (magnitude) of the vector """
		return math.sqrt(sum(comp ** 2 for comp in self))

	def scale(self, scaleby):
		""" Scales Vector by some value """
		return self.__class__(*[x * scaleby for x in self.values])

	def extend(self, direction, scale):
		""" Extends Vector in a direction multiplied by a scale """
		if type(self) != type(direction):
			return NotImplemented
		return self.__class__(*[a + (b * scale) for a, b in zip(self.values, direction)])

	def argument(self):
		""" Returns the argument of the vector, the angle clockwise from +y."""
		arg_in_rad = math.acos(self.__class__(0, 1) * self / self.length())
		arg_in_deg = math.degrees(arg_in_rad)
		if self.values[0] < 0:
			return 360 - arg_in_deg
		else:
			return arg_in_deg

	def normalize(self):
		""" Returns a normalized unit vector """
		length = self.length()
		if length == 0:
			return self.__class__(*[0 for i in self.values])
		return self.__class__(*[comp / length for comp in self])

	def rotate(self, *args):
		""" Rotate this vector. If passed a number, assumes this is a
			2D vector and rotates by the passed value in degrees.  Otherwise,
			assumes the passed value is a list acting as a matrix which rotates the vector.
		"""
		#https://gist.github.com/mcleonard/5351452#gistcomment-2975482
		if len(args) == 1 and isinstance(args[0], (float, int)):
			# So, if rotate is passed an int or a float...
			if len(self) != 2:
				raise ValueError("Rotation axis not defined for greater than 2D vector")
			return self._rotate2D(*args)
		elif len(args) == 1:
			matrix = args[0]
			#https://gist.github.com/mcleonard/5351452#gistcomment-1559013
			if not all(len(row) == len(matrix) for row in matrix) or not len(matrix) == len(self):
				raise ValueError("Rotation matrix must be square and same dimensions as vector")
			return self.matrix_mult(matrix)

	def _rotate2D(self, theta):
		""" Rotate this vector by theta in degrees.

			Returns a new vector.
		"""
		theta = math.radians(theta)
		# Just applying the 2D rotation matrix
		dc, ds = math.cos(theta), math.sin(theta)
		x, y = self.values
		x, y = dc * x - ds * y, ds * x + dc * y
		return self.__class__(x, y)

	def matrix_mult(self, matrix):
		""" Multiply this vector by a matrix.  Assuming matrix is a list of lists.

			Example:
			mat = [[1,2,3],[-1,0,1],[3,4,5]]
			Vector(1,2,3).matrix_mult(mat) ->  (14, 2, 26)

		"""
		if not all(len(row) == len(self) for row in matrix):
			raise ValueError('Matrix must match vector dimensions')

		# Grab a row from the matrix, make it a Vector, take the dot product,
		# and store it as the first component
		product = tuple(self.__class__(*row) * self for row in matrix)

		return self.__class__(*product)

	def cross(self, other):
		""" Returns the cross product of self and other vector (Only for 3 dimentional vectors)
		"""
		if len(self.values) != 3:
			raise ValueError('Vectors must be 3 dimentional to calculate cross product')

		xh = self.y * other.z - other.y * self.z
		yh = self.z * other.x - other.z * self.x
		zh = self.x * other.y - other.x * self.y
		return self.__class__(*[xh, yh, zh])

	def inner(self, other):
		""" Returns the dot product (inner product) of self and other vector
		"""
		return sum(a * b for a, b in zip(self, other))

	def close_enough(self, other, eps):
		return True if len([a for a, b in zip(self.values, other) if -eps <= abs(a) - abs(b) <= eps]) == len(self.values) else False

	def normalize_toscale(self):
		return self.__class__(*(self / max(self)))

	def __mul__(self, other):
		""" Returns the dot product of self and other if multiplied
			by another Vector.  If multiplied by an int or float,
			multiplies each component by other.
		"""
		#https://gist.github.com/mcleonard/5351452#gistcomment-2975482
		if isinstance(other, type(self)):
			return self.inner(other)
		elif isinstance(other, (float, int)):
			product = tuple(a * other for a in self)
			return self.__class__(*product)

	def __rmul__(self, other):
		""" Called if 4*self for instance """
		return self.__mul__(other)

	def __truediv__(self, other):
		#https://gist.github.com/mcleonard/5351452#gistcomment-2975482
		if isinstance(other, (float, int)):
			divided = tuple(a / other for a in self)
			return self.__class__(*divided)

	def __add__(self, other):
		""" Returns the vector addition of self and other """
		added = tuple(a + b for a, b in zip(self, other))
		return self.__class__(*added)

	def __sub__(self, other):
		""" Returns the vector difference of self and other """
		subbed = tuple(a - b for a, b in zip(self, other))
		return self.__class__(*subbed)

	def __pow__(self, power, modulo=None):
		if isinstance(power, (float, int)):
			result = tuple(a ** power for a in self)
			return self.__class__(*result)

	def __neg__(self):
		negated = tuple(-a if a != 0 else a for a in self)
		return self.__class__(*negated)

	def __iter__(self):
		return self.values.__iter__()

	def __len__(self):
		return len(self.values)

	def __getitem__(self, key):
		return self.values[key]

	def __setitem__(self, key, value):
		self.values[key] = value

	def __repr__(self):
		return str(self.values)

	def __eq__(self, other):
		return True if [a for a, b in zip(self, other) if a == b] else False

	#https://gist.github.com/mcleonard/5351452#gistcomment-3032580
	@property
	def x(self):
		""" Returns the first vector component """
		return self.values[0]

	@property
	def y(self):
		""" Returns the second vector component """
		return self.values[1]

	@property
	def z(self):
		""" Returns the third vector component """
		return self.values[2]

	@property
	def w(self):
		""" Returns the fourth vector component """
		return self.values[3]
