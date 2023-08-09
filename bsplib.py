import enum
import struct
import abc
from vector import Vector


class BSPLumps(enum.IntEnum):
	LUMP_ENTITIES = 0,
	LUMP_PLANES = 1,
	LUMP_TEXDATA = 2,
	LUMP_VERTEXES = 3,
	LUMP_VISIBILITY = 4,
	LUMP_NODES = 5,
	LUMP_TEXINFO = 6,
	LUMP_FACES = 7,
	LUMP_LIGHTING = 8,
	LUMP_OCCLUSION = 9,
	LUMP_LEAFS = 10,
	LUMP_FACEIDS = 11,
	LUMP_EDGES = 12,
	LUMP_SURFEDGES = 13,
	LUMP_MODELS = 14,
	LUMP_WORLDLIGHTS = 15,
	LUMP_LEAFFACES = 16,
	LUMP_LEAFBRUSHES = 17,
	LUMP_BRUSHES = 18,
	LUMP_BRUSHSIDES = 19,
	LUMP_AREAS = 20,
	LUMP_AREAPORTALS = 21,
	LUMP_FACEBRUSHES = 22,
	LUMP_FACEBRUSHLIST = 23,
	LUMP_UNUSED1 = 24,
	LUMP_UNUSED2 = 25,
	LUMP_DISPINFO = 26,
	LUMP_ORIGINALFACES = 27,
	LUMP_PHYSDISP = 28,
	LUMP_PHYSCOLLIDE = 29,
	LUMP_VERTNORMALS = 30,
	LUMP_VERTNORMALINDICES = 31,
	LUMP_DISP_LIGHTMAP_ALPHAS = 32,
	LUMP_DISP_VERTS = 33,
	LUMP_DISP_LIGHTMAP_SAMPLE_POSITIONS = 34,
	LUMP_GAME_LUMP = 35,
	LUMP_LEAFWATERDATA = 36,
	LUMP_PRIMITIVES = 37,
	LUMP_PRIMVERTS = 38,
	LUMP_PRIMINDICES = 39,
	LUMP_PAKFILE = 40,
	LUMP_CLIPPORTALVERTS = 41,
	LUMP_CUBEMAPS = 42,
	LUMP_TEXDATA_STRING_DATA = 43,
	LUMP_TEXDATA_STRING_TABLE = 44,
	LUMP_OVERLAYS = 45,
	LUMP_LEAFMINDISTTOWATER = 46,
	LUMP_FACE_MACRO_TEXTURE_INFO = 47,
	LUMP_DISP_TRIS = 48,
	LUMP_PROP_BLOB = 49,
	LUMP_WATEROVERLAYS = 50,
	LUMP_LEAF_AMBIENT_INDEX_HDR = 51,
	LUMP_LEAF_AMBIENT_INDEX = 52,
	LUMP_LIGHTING_HDR = 53,
	LUMP_WORLDLIGHTS_HDR = 54,
	LUMP_LEAF_AMBIENT_LIGHTING_HDR = 55,
	LUMP_LEAF_AMBIENT_LIGHTING = 56,
	LUMP_XZIPPAKFILE = 57,
	LUMP_FACES_HDR = 58,
	LUMP_MAP_FLAGS = 59,
	LUMP_OVERLAY_FADES = 60,
	LUMP_OVERLAY_SYSTEM_LEVELS = 61,
	LUMP_PHYSLEVEL = 62,
	LUMP_DISP_MULTIBLEND = 63,
	HEADER_LUMPS = 64


class SURFFlags(enum.IntFlag):
	SURF_LIGHT = 0x0001  # value will hold the light strength
	SURF_SKY2D = 0x0002  # don't draw, indicates we should skylight + draw 2d sky but not draw the 3D skybox
	SURF_SKY = 0x0004  # don't draw, but add to skybox
	SURF_WARP = 0x0008  # turbulent water warp
	SURF_TRANS = 0x0010
	SURF_NOPORTAL = 0x0020  # the surface can not have a portal placed on it
	SURF_TRIGGER = 0x0040
	SURF_NODRAW = 0x0080  # don't bother referencing the texture
	SURF_HINT = 0x0100  # make a primary bsp splitter
	SURF_SKIP = 0x0200  # completely ignore, allowing non-closed brushes
	SURF_NOLIGHT = 0x0400  # Don't calculate light
	SURF_BUMPLIGHT = 0x0800  # calculate three lightmaps for the surface for bumpmapping
	SURF_NOSHADOWS = 0x1000  # Don't receive shadows
	SURF_NODECALS = 0x2000  # Don't receive decals
	SURF_NOPAINT = 0x2000  # the surface can not have paint placed on it
	SURF_NOCHOP = 0x4000  # Don't subdivide patches on this surface
	SURF_HITBOX = 0x8000  # surface is part of a hitbox


class EmitType(enum.IntEnum):
	emit_surface = 0  # 90 degree spotlight
	emit_point = enum.auto()  # simple point light source
	emit_spotlight = enum.auto()  # spotlight with penumbra
	emit_skylight = enum.auto()  # directional light with no falloff (surface must trace to SKY texture)
	emit_quakelight = enum.auto()  # linear falloff, non-lambertian
	emit_skyambient = enum.auto()  # spherical light source with no falloff (surface must trace to SKY texture)


class ByteSection(abc.ABC):
	def __init__(self, data):
		pass

	@classmethod
	def __frombytes__(cls, bytedata, definition):
		assert len(bytedata) % cls.byte_size() == 0, f"Wrong sized bytedata passed to {cls.__name__} struct ({len(bytedata)} % {cls.byte_size()} != 0)!"
		return struct.unpack(definition, bytedata)

	@classmethod
	@abc.abstractmethod
	def frombytes(cls, bytedata):
		pass

	@staticmethod
	@abc.abstractmethod
	def byte_size():
		pass

	@staticmethod
	def iterate_all():
		return True

	def __repr__(self):
		return "<{0}: [\n\t{1}\n]>".format(
			self.__class__.__name__,
			",\n\t".join("{} = {!r}".format(k, v).replace("\n", "\n\t") for k, v in self.__dict__.items())
		)


class BSPFile(ByteSection):
	def __init__(self, data):
		super().__init__(data)
		self.raw_data = data[0]
		self.ident = data[1]
		self.version = data[2]
		self.lumps = data[3]
		self.map_revision = data[4]

	@classmethod
	def frombytes(cls, bytedata):
		assert len(bytedata) >= cls.byte_size(), f"Wrong sized bytedata passed to {cls.__name__} struct! ({len(bytedata)} < {cls.byte_size()})"
		data = struct.unpack("2I", bytedata[0:8])

		# VBSP check
		assert data[0] == 0x50534256, "Not a bsp file were specified!"

		lumps = []
		unresolved_lumps = []

		for i in range(BSPLumps.HEADER_LUMPS):
			lump = lump_t.frombytes(bytedata[(i * 16) + 8:((i + 1) * 16) + 8])
			lumps.append(lump)

			if i in lumps_mapping:
				if lump.filelen > 0:
					if type(lumps_mapping[BSPLumps(i)]) == dict:
						assert lump.version in lumps_mapping[BSPLumps(i)], f"Invalid or unsupported lump version {lump.version} for {str(BSPLumps(i))}."
						ctype = lumps_mapping[BSPLumps(i)][lump.version]
					else:
						ctype = lumps_mapping[BSPLumps(i)]

					if ctype.iterate_all():
						assert lump.filelen % ctype.byte_size() == 0, f"Failed to parse {str(BSPLumps(i))}, bogus section size ({lump.filelen} % {ctype.byte_size()})."
						lump.data = []

						for j in range(0, lump.filelen, ctype.byte_size()):
							total_size = lump.fileofs + j
							lump.data.append(ctype.frombytes(bytedata[total_size:total_size + ctype.byte_size()]))
					else:
						lump.data = ctype.frombytes(bytedata[lump.fileofs:lump.fileofs + lump.filelen])
				else:
					unresolved_lumps.append(i)

		# In some cases there's 0 length set for a lump, but data is there,
		# so calculate closest lump and get length from their positions
		for ulidx in unresolved_lumps:
			closest = 0
			for i in range(BSPLumps.HEADER_LUMPS):
				if (closest == 0 and lumps[i].fileofs > lumps[ulidx].fileofs) or (closest > lumps[i].fileofs > lumps[ulidx].fileofs):
					closest = lumps[i].fileofs

			lump = lumps[ulidx]
			lump.filelen = closest - lump.fileofs
			assert lump.filelen > 0, f"Found lump with no size ({str(BSPLumps(ulidx))}), and wasn't able to fix lump size (estimated: {lump.filelen})"

			print(f"Found lump with no size ({str(BSPLumps(ulidx))}), new estimated size = {lump.filelen}.")

			if type(lumps_mapping[BSPLumps(ulidx)]) == dict:
				assert lump.version in lumps_mapping[
					BSPLumps(ulidx)], f"Invalid or unsupported lump version {lump.version} for {str(BSPLumps(ulidx))}."
				ctype = lumps_mapping[BSPLumps(ulidx)][lump.version]
			else:
				ctype = lumps_mapping[BSPLumps(ulidx)]

			if ctype.iterate_all():
				assert lump.filelen % ctype.byte_size() == 0, f"Failed to parse {str(BSPLumps(ulidx))}, bogus section size ({lump.filelen} % {ctype.byte_size()})."
				lump.data = []

				for j in range(0, lump.filelen, ctype.byte_size()):
					lump.data.append(
						ctype.frombytes(bytedata[lump.fileofs + j:lump.fileofs + j + ctype.byte_size()]))
			else:
				lump.data = ctype.frombytes(bytedata[lump.fileofs:lump.fileofs + lump.filelen])

		return cls([bytedata, data[0], data[1], lumps, struct.unpack("I", bytedata[-4:])[0]])

	@staticmethod
	def byte_size():
		return 1036


class lump_t(ByteSection):
	def __init__(self, data):
		super().__init__(data)
		self.fileofs = data[0]
		self.filelen = data[1]
		self.version = data[2]
		self.fourCC = data[3:7]
		self.data = None

	@classmethod
	def frombytes(cls, bytedata):
		return cls(super().__frombytes__(bytedata, "3I4b"))

	@staticmethod
	def byte_size():
		return 16


class dplane_t(ByteSection):
	def __init__(self, data):
		super().__init__(data)
		self.normal = Vector(*data[0:3])
		self.dist = data[3]
		self.type = data[4]

	@classmethod
	def frombytes(cls, bytedata):
		return cls(super().__frombytes__(bytedata, "4fi"))

	@staticmethod
	def byte_size():
		return 20


class dtexdata_t(ByteSection):
	def __init__(self, data):
		super().__init__(data)
		self.reflectivity = Vector(*data[0:3])
		self.nameStringTableID = data[3]
		self.width = data[4]
		self.height = data[5]
		self.view_width = data[6]
		self.view_height = data[7]

	@classmethod
	def frombytes(cls, bytedata):
		return cls(super().__frombytes__(bytedata, "3f5I"))

	@staticmethod
	def byte_size():
		return 32


class dvertex_t(ByteSection):
	def __init__(self, data):
		super().__init__(data)
		self.point = Vector(*data[0:3])

	@classmethod
	def frombytes(cls, bytedata):
		return cls(super().__frombytes__(bytedata, "3f"))

	@staticmethod
	def byte_size():
		return 12


class texinfo_t(ByteSection):
	def __init__(self, data):
		super().__init__(data)
		self.textureVecsTexelsPerWorldUnits = (data[0:4], data[4:8])
		self.lightmapVecsLuxelsPerWorldUnits = (data[8:12], data[12:16])
		self.flags = data[16]
		self.texdata = data[17]

	@classmethod
	def frombytes(cls, bytedata):
		return cls(super().__frombytes__(bytedata, "16f2I"))

	@staticmethod
	def byte_size():
		return 72


class dface_t(ByteSection):
	def __init__(self, data):
		super().__init__(data)
		self.planenum = data[0]
		self.side = data[1]
		self.onNode = data[2]
		self.firstedge = data[3]
		self.numedges = data[4]
		self.texinfo = data[5]
		self.dispinfo = data[6]
		self.surfaceFogVolumeID = data[7]
		self.styles = data[8:12]
		self.lightofs = data[12]
		self.area = data[13]
		self.m_LightmapTextureMinsInLuxels = data[14:16]
		self.m_LightmapTextureSizeInLuxels = data[16:18]
		self.origFace = data[18]
		self.numPrims = data[19]
		self.firstPrimID = data[20]
		self.smoothingGroups = data[21]

	@classmethod
	def frombytes(cls, bytedata):
		return cls(super().__frombytes__(bytedata, "H2bi4h4bif5i2HI"))

	@staticmethod
	def byte_size():
		return 56


class dedge_t(ByteSection):
	def __init__(self, data):
		super().__init__(data)
		self.v = data

	@classmethod
	def frombytes(cls, bytedata):
		return cls(super().__frombytes__(bytedata, "2H"))

	@staticmethod
	def byte_size():
		return 4


class surfedges_t(ByteSection):
	@classmethod
	def frombytes(cls, bytedata):
		return super().__frombytes__(bytedata, "%di" % (len(bytedata) / cls.byte_size()))

	@staticmethod
	def byte_size():
		return 4

	@staticmethod
	def iterate_all():
		return False


class dworldlight_t(ByteSection):
	def __init__(self, data):
		super().__init__(data)
		self.origin = Vector(*data[0:3])
		self.intensity = Vector(*data[3:6])
		self.normal = Vector(*data[6:9])
		self.shadow_cast_offset = Vector(*data[9:12])
		self.cluster = data[12]
		self.type = data[13]
		self.style = data[14]
		self.stopdot = data[15]
		self.stopdot2 = data[16]
		self.exponent = data[17]
		self.radius = data[18]
		self.constant_attn = data[19]
		self.linear_attn = data[20]
		self.quadratic_attn = data[21]
		self.flags = data[22]
		self.texinfo = data[23]
		self.owner = data[24]

	@classmethod
	def frombytes(cls, bytedata):
		return cls(super().__frombytes__(bytedata, "12f3I7f3I"))

	@staticmethod
	def byte_size():
		return 100


class dworldlight_t_ver0(ByteSection):
	def __init__(self, data):
		super().__init__(data)
		self.origin = Vector(*data[0:3])
		self.intensity = Vector(*data[3:6])
		self.normal = Vector(*data[6:9])
		self.cluster = data[9]
		self.type = data[10]
		self.style = data[11]
		self.stopdot = data[12]
		self.stopdot2 = data[13]
		self.exponent = data[14]
		self.radius = data[15]
		self.constant_attn = data[16]
		self.linear_attn = data[17]
		self.quadratic_attn = data[18]
		self.flags = data[19]
		self.texinfo = data[20]
		self.owner = data[21]

	@classmethod
	def frombytes(cls, bytedata):
		return cls(super().__frombytes__(bytedata, "9f3I7f3I"))

	@staticmethod
	def byte_size():
		return 88


class dbrush_t(ByteSection):
	def __init__(self, data):
		super().__init__(data)
		self.firstside = data[0]
		self.numsides = data[1]
		self.contents = data[2]

	@classmethod
	def frombytes(cls, bytedata):
		return cls(super().__frombytes__(bytedata, "3I"))

	@staticmethod
	def byte_size():
		return 12


class dbrushside_t(ByteSection):
	def __init__(self, data):
		super().__init__(data)
		self.planenum = data[0]
		self.texinfo = data[1]
		self.dispinfo = data[2]
		self.bevel = data[3]
		self.thin = data[4]

	@classmethod
	def frombytes(cls, bytedata):
		return cls(super().__frombytes__(bytedata, "H2h2b"))

	@staticmethod
	def byte_size():
		return 8


class stringdata_t(ByteSection):
	def __init__(self, data):
		super().__init__(data)
		self.__data = data

	@classmethod
	def frombytes(cls, bytedata):
		return cls(bytedata.decode("utf-8"))

	@staticmethod
	def byte_size():
		# max possible size in this case
		# unused
		return 128

	@staticmethod
	def iterate_all():
		return False

	def __getitem__(self, key):
		if isinstance(key, slice):
			indices = range(*key.indices(len(self.__data)))
			name = "".join([self.__data[i] for i in indices])
			return name[:name.find('\x00')]
		return self.__data[key]


class stringtable_t(ByteSection):
	@classmethod
	def frombytes(cls, bytedata):
		return super().__frombytes__(bytedata, "%di" % (len(bytedata) / cls.byte_size()))

	@staticmethod
	def byte_size():
		return 4

	@staticmethod
	def iterate_all():
		return False


"""
	Too lazy to add all lump definitions, so if you need them, 
	you can impliment them pretty easily:
	First, define your class structure same as bsp file is using,
	you can find all definitions here: https://github.com/alliedmodders/hl2sdk/blob/sdk2013/public/bspfile.h
	Make sure to inherit from ByteSection and impliment byte_size() and frombytes() methods as they are used
	to parse .bsp file, you can use other structures as an example for your own.
	After structure definition is done, you need to add it into lumps_mapping variable,
	it is simple key value dictionary, where key is a lump and value is structure
	associated with it. And you are done with it, if everything done correctly,
	.bsp should be parsed successfully with your lump structure.
	Note: If your structure has multiple versions you can define all them in another dictionary
	where each key is version number and value is associated structure. (eg. LUMP_WORLDLIGHTS)
	Note2: In case you don't want parser to parse whole lump just by iterating it, cuz
	for example you have dynamic structure, or you don't want to have class members cuz
	lump is a simple int or whatever, declare iterate_all() method that returns False,
	this will prevent parser from itereting whole lump, and will leave parsing to you, 
	so you should define how parsing should be done yourself inside frombytes() method,
	byte_size() in this case isn't called (only if you don't call super().__frombytes__())
	and you can leave whatever you want there. (eg. LUMP_TEXDATA_STRING_DATA, LUMP_TEXDATA_STRING_TABLE, LUMP_SURFEDGES)
"""

lumps_mapping = {
	BSPLumps.LUMP_PLANES: dplane_t,
	BSPLumps.LUMP_TEXDATA: dtexdata_t,
	BSPLumps.LUMP_VERTEXES: dvertex_t,
	BSPLumps.LUMP_TEXINFO: texinfo_t,
	BSPLumps.LUMP_FACES: dface_t,
	BSPLumps.LUMP_EDGES: dedge_t,
	BSPLumps.LUMP_SURFEDGES: surfedges_t,
	BSPLumps.LUMP_WORLDLIGHTS: {0: dworldlight_t_ver0, 1: dworldlight_t},
	BSPLumps.LUMP_BRUSHES: dbrush_t,
	BSPLumps.LUMP_BRUSHSIDES: dbrushside_t,
	BSPLumps.LUMP_TEXDATA_STRING_DATA: stringdata_t,
	BSPLumps.LUMP_TEXDATA_STRING_TABLE: stringtable_t
}
