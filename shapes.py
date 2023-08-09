from vector import Vector


maxchop = 4
minchop = 4

class Polygon:
	def __init__(self, _points: list, _chop = maxchop, _normal = Vector(0, 0, 0)):
		assert len(_points) >= 3, f"Wrong polygon being constructed. ({len(_points)} < 3)"
		self.points = _points

		self.normal = _normal
		if self.normal == Vector(0, 0, 0):
			self.calc_normal()

		self.mins = Vector(0, 0, 0)
		self.maxs = Vector(0, 0, 0)
		self.calc_bounds()

		self.chop = _chop

		self.area = 0
		self.center = Vector(0, 0, 0)
		self.calc_area_and_center()

	def calc_normal(self):
		norm = Vector(0, 0, 0)
		numverts = len(self.points)

		for i in range(numverts):
			norm = norm + Vector(*[
				(self.points[i].y - self.points[(i + 1) % numverts].y) * (self.points[i].z + self.points[(i + 1) % numverts].z),
				(self.points[i].z - self.points[(i + 1) % numverts].z) * (self.points[i].x + self.points[(i + 1) % numverts].x),
				(self.points[i].x - self.points[(i + 1) % numverts].x) * (self.points[i].y + self.points[(i + 1) % numverts].y)
			])

		self.normal = -norm.normalize()

	def calc_bounds(self):
		self.mins = Vector(*self.points[0])
		self.maxs = Vector(*self.points[0])
		for point in self.points[0:]:
			for i in range(3):
				if point[i] < self.mins[i]:
					self.mins[i] = point[i]
				if point[i] > self.maxs[i]:
					self.maxs[i] = point[i]

	def calc_area_and_center(self):
		total = 0
		for p0, p1, p2 in self.iter_as_tris():
			area = (p1 - p0).cross(p2 - p1).length()
			total = total + area
			self.center = self.center.extend(p1, area / 3).extend(p2, area / 3).extend(p0, area / 3)

		if total != 0:
			self.center = self.center.scale(1 / total)

		self.area = total * 0.5

		assert self.area > 0, "Zero area child patch!!!!"

	def subdivide(self, luxscale, subpatches_list):
		widest = -1
		widest_axis = -1
		subdiv = False
		total = (self.maxs - self.mins).scale(luxscale)

		for i in range(3):
			if total[i] > widest:
				widest_axis = i
				widest = total[i]

			if total[i] >= self.chop and total[i] >= minchop:
				subdiv = True

		if not subdiv and widest_axis != -1:
			if total[widest_axis] > total[(widest_axis + 1) % 3] * 2 and total[widest_axis] > total[(widest_axis + 2) % 3] * 2:
				if self.chop > minchop:
					subdiv = True
					self.chop = max([minchop, self.chop / 2])

		if not subdiv:
			subpatches_list.append(self)
			return None

		split = Vector(0, 0, 0)
		split[widest_axis] = 1
		dist = (self.mins[widest_axis] + self.maxs[widest_axis]) * 0.5
		o1, o2 = self.clip_epsilon(split, dist, 0.1)

		if o1 is not None:
			o1.subdivide(luxscale, subpatches_list)
		if o2 is not None:
			o2.subdivide(luxscale, subpatches_list)

		return subpatches_list

	def clip_epsilon(self, normal, dist, epsilon):
		sides = [0 for i in range(68)]
		dists = [0 for i in range(68)]
		counts = [0 for i in range(3)]

		for i, point in enumerate(self.points):
			dot = (point * normal) - dist
			dists[i] = dot
			if dot > epsilon:
				sides[i] = 0
			elif dot < -epsilon:
				sides[i] = 1
			else:
				sides[i] = 2
			counts[sides[i]] = counts[sides[i]] + 1

		sides[len(self.points)] = sides[0]
		dists[len(self.points)] = dists[0]

		if counts[0] == 0:
			return None, self

		if counts[1] == 0:
			return self, None

		f = []
		b = []
		mid = Vector(0, 0, 0)

		for i, point in enumerate(self.points):
			if sides[i] == 2:
				f.append(Vector(*point))
				b.append(Vector(*point))
				continue

			if sides[i] == 0:
				f.append(Vector(*point))

			if sides[i] == 1:
				b.append(Vector(*point))

			if sides[i + 1] == 2 or sides[i + 1] == sides[i]:
				continue

			p2 = self.points[(i + 1) % len(self.points)]
			dot = dists[i] / (dists[i] - dists[i + 1])
			for j in range(3):
				if normal[j] == 1:
					mid[j] = dist
				elif normal[j] == -1:
					mid[j] = -dist
				else:
					mid[j] = point[j] + dot * (p2[j] - point[j])

			f.append(Vector(*mid))
			b.append(Vector(*mid))

		assert len(f) <= len(self.points) + 4 and len(b) <= len(self.points) + 4, "Maximum points exceeded on clip epsilon. Probably some logic issue!"
		assert len(f) <= 64 and len(b) <= 64, "Maximum points exceeded on clip epsilon. Probably some logic issue!"

		if len(f) >= 3 and len(b) >= 3:
			return Polygon(f), Polygon(b)
		elif len(f) >= 3:
			return Polygon(f), None
		elif len(b) >= 3:
			return None, Polygon(b)

		assert False, "Some logic issue, this code shouldn't be triggered!"

	def is_intersect(self, l1, l2):
		for p0, p1, p2 in self.iter_as_tris():
			p01 = p1 - p0
			p02 = p2 - p0
			l12 = l2 - l1

			# https://en.wikipedia.org/wiki/Line%E2%80%93plane_intersection
			# 1e-10 added to eliminate possible division by zero
			t = (p01.cross(p02) * (l1 - p0)) / ((p01.cross(p02) * -l12) + 1e-10)
			u = (p02.cross(-l12) * (l1 - p0)) / ((p01.cross(p02) * -l12) + 1e-10)
			v = ((-l12).cross(p01) * (l1 - p0)) / ((p01.cross(p02) * -l12) + 1e-10)

			if 0 <= t <= 1 and 0 <= u <= 1 and 0 <= v <= 1 and u + v <= 1:
				return True
		return False

	def iter_as_tris(self):
		for i in range(1, len(self.points) - 1):
			yield self.points[0], self.points[i], self.points[i + 1]

	def __repr__(self):
		return "<{0}: [\n\t{1}\n]>".format(
			self.__class__.__name__,
			",\n\t".join("{} = {!r}".format(k, v).replace("\n", "\n\t") for k, v in self.__dict__.items())
		)


class Shape:
	def __init__(self, _polys: list):
		self.polys = _polys

	@classmethod
	def extrude_poly_to_shape(cls, poly, width):
		polys = [poly]
		numverts = len(poly.points)

		for i, point in enumerate(poly.points):
			polys.append(Polygon([
				point, poly.points[(i + 1) % numverts],
				poly.points[(i + 1) % numverts] + (width * poly.normal),
				point + (width * poly.normal)
			]))

		polys.append(Polygon([x + (poly.normal * width) for x in poly.points[::-1]]))

		return cls(polys)

	@classmethod
	def subdivide_poly_to_shape(cls, poly, luxscale):
		patches = []
		poly.subdivide(luxscale, patches)
		return cls(patches)

	def is_inside(self, point):
		dest = self.polys[0].points[0].extend(-self.polys[0].normal, 30)
		intersections = 0
		last_hit_poly = 0
		for poly in self.polys:
			if poly.is_intersect(point, dest):
				intersections = intersections + 1
				last_hit_poly = poly

		if intersections % 2 == 1:
			return last_hit_poly
		else:
			return None

	def close_enough(self, point, eps):
		for poly in self.polys:
			if poly.center.close_enough(point, eps):
				return poly

	def __repr__(self):
		return "<{0}: [\n\t{1}\n]>".format(self.__class__.__name__, "\n\t".join([str(x) for x in self.polys]))