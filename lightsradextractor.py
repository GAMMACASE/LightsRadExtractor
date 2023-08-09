import os
import math
import time
from bsplib import *
from shapes import Polygon, Shape
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter

ProcessArgs = None

def main():
	starttime = time.time()

	for path in ProcessArgs.filepath:
		if not os.path.exists(path):
			print(f"No file were found under {path} path, skipping...")
			continue

		with open(path, "rb") as inp:
			try:
				print(f"Parsing {path}:")
				bsp = BSPFile.frombytes(inp.read())
			except Exception as e:
				print(f"{e}, skipping...")
				continue

		edges = bsp.lumps[BSPLumps.LUMP_EDGES].data
		surfedges = bsp.lumps[BSPLumps.LUMP_SURFEDGES].data
		verts = bsp.lumps[BSPLumps.LUMP_VERTEXES].data
		texinfo = bsp.lumps[BSPLumps.LUMP_TEXINFO].data
		texdata = bsp.lumps[BSPLumps.LUMP_TEXDATA].data
		stringdata = bsp.lumps[BSPLumps.LUMP_TEXDATA_STRING_DATA].data
		stringtable = bsp.lumps[BSPLumps.LUMP_TEXDATA_STRING_TABLE].data
		faces = bsp.lumps[BSPLumps.LUMP_FACES].data

		shapes = []
		foundtextures = []

		for faceidx, face in enumerate(bsp.lumps[BSPLumps.LUMP_FACES].data):
			tx: texinfo_t = texinfo[face.texinfo]
			if tx.flags & SURFFlags.SURF_LIGHT:
				txdata: dtexdata_t = texdata[tx.texdata]
				texture = stringdata[stringtable[txdata.nameStringTableID]:]

				if ProcessArgs.quick_search and texture in foundtextures:
					continue

				surfedges_list = []
				chopscale = [0, 0]

				for i in range(2):
					for j in range(3):
						chopscale[i] = chopscale[i] + (tx.lightmapVecsLuxelsPerWorldUnits[i][j] ** 2)
					chopscale[i] = math.sqrt(chopscale[i])

				for i in range(face.numedges):
					edgeidx = surfedges[face.firstedge + i]
					points = edges[abs(edgeidx)].v

					surfedges_list.append(verts[points[1 if edgeidx < 0 else 0]].point)

				try:
					shapes.append((Shape.subdivide_poly_to_shape(Polygon(surfedges_list), (chopscale[0] + chopscale[1]) / 2), faceidx))
				except Exception as e:
					print('Failed to construct a Shape. Reason:', e)
				foundtextures.append(texture)

		foundtextures = dict()
		lights = list(bsp.lumps[BSPLumps.LUMP_WORLDLIGHTS].data)

		for light in lights:
			if light.type == EmitType.emit_surface:
				for shape, faceidx in shapes:
					face: dface_t = faces[faceidx]
					tx: texinfo_t = texinfo[face.texinfo]
					txdata: dtexdata_t = texdata[tx.texdata]
					texture = stringdata[stringtable[txdata.nameStringTableID]:]

					if texture in foundtextures:
						shapes.remove((shape, faceidx))
						continue

					poly: Polygon = shape.close_enough(light.origin, ProcessArgs.search_distance)

					if poly is not None:
						scale = [0, 0]
						for i in range(2):
							for j in range(3):
								scale[i] = scale[i] + (tx.textureVecsTexelsPerWorldUnits[i][j] ** 2)
							scale[i] = math.sqrt(scale[i])

						basecolor = (light.intensity * 255 / (100 * 100)) * (txdata.width * txdata.height / (scale[0] * scale[1] * poly.area))

						# Here's few variations of code where all produce different results
						# the one currently used is the most consistent one that produces 100% match to the original
						"""rgb = light.intensity.normalize_toscale()
						realrgb = ((rgb / 255) ** (1 / 2.2)) * 255
						foundtextures[texture] = [realrgb, round(max(basecolor) / max(rgb))]"""

						"""clr = light.intensity.normalize() ** (1 / 2.2)
						newclr = clr
						if max(clr) > 1.0:
							newclr = newclr.scale(1 / max(clr))
						foundtextures[texture] = [newclr.scale(255).scale(((round(max(basecolor) / max(rgb)) ** 0.85) * 0.002) + 1), round(max(basecolor) / max(rgb))]"""
						
						realrgb = ((basecolor / 255) ** (1 / 2.2)) * 255
						realrgb = Vector(*[round(x) for x in realrgb])
						foundtextures[texture] = [realrgb]

						lights.remove(light)
						shapes.remove((shape, faceidx))

						break

		if len(foundtextures) > 0:
			with open(os.path.join(os.path.dirname(path), f"lights_{os.path.splitext(os.path.basename(path))[0]}.rad"), "w") as out:
				print(f"Found {len(foundtextures)} textures:")
				for key, value in foundtextures.items():
					msg = f"{key.lower()} {' '.join([str(x) for x in value[0]])}"
					print(f"{msg}")
					out.write(f"{msg}\n")
		else:
			print(f"No light.rad textures were found!")

	input(f"Program finished in {time.time() - starttime:.3f} seconds. Press ENTER to exit...")


if __name__ == "__main__":
	parser = ArgumentParser(description = 'Extracts lights.rad information from a Source 1 Engine maps.', formatter_class = ArgumentDefaultsHelpFormatter)
	parser.add_argument('-q', '--quick_search',
			help = 'Performs quick search, faster but might not find everything;',
			action = 'store_true', default = False, dest = 'quick_search')
	parser.add_argument('-d', '--distance',
			help = 'Distance to search for the light in units, increasing it might help searching for textures with quick_search enabled. (bhop_bludi (CSS) with quick search, needs this set to 5 to find the texture for example);',
			action = 'store', type = int, default = 1, dest = 'search_distance')
	parser.add_argument('-v', '--version', action = 'version', version = 'LightsRadExtractor 1.0.0')
	parser.add_argument('filepath', help = 'Paths to bsp file;', nargs = '+')
	
	ProcessArgs = parser.parse_args()

	main()