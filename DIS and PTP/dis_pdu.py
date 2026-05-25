import struct
import time
from dataclasses import dataclass, field

DIS_VERSION = 7
PDU_TYPE_ENTITY_STATE = 1
PROTOCOL_FAMILY_ENTITY_INFORMATION = 1
DEFAULT_EXERCISE_ID = 1
_TICKS_PER_HOUR = (2**31) - 1


def dis_timestamp_absolute() -> int:
    now = time.time()
    seconds_in_hour = now % 3600.0
    ticks = int((seconds_in_hour / 3600.0) * _TICKS_PER_HOUR)
    return (ticks << 1) | 1


@dataclass
class EntityID:
    site: int = 1
    application: int = 1
    entity: int = 1


@dataclass
class EntityType:
    kind: int = 1
    domain: int = 2
    country: int = 0
    category: int = 0
    subcategory: int = 0
    specific: int = 0
    extra: int = 0


@dataclass
class Vec3f:
    x: float
    y: float
    z: float


@dataclass
class Vec3d:
    x: float
    y: float
    z: float


@dataclass
class Orientation:
    psi: float
    theta: float
    phi: float


@dataclass
class EntityStatePDU:
    protocol_version: int = DIS_VERSION
    exercise_id: int = DEFAULT_EXERCISE_ID
    pdu_type: int = PDU_TYPE_ENTITY_STATE
    protocol_family: int = PROTOCOL_FAMILY_ENTITY_INFORMATION
    timestamp: int = 0
    length: int = 144

    entity_id: EntityID = field(default_factory=EntityID)
    force_id: int = 0
    num_articulation_params: int = 0
    entity_type: EntityType = field(default_factory=EntityType)
    alt_entity_type: EntityType = field(default_factory=EntityType)
    linear_velocity: Vec3f = field(default_factory=lambda: Vec3f(0.0, 0.0, 0.0))
    location: Vec3d = field(default_factory=lambda: Vec3d(0.0, 0.0, 0.0))
    orientation: Orientation = field(default_factory=lambda: Orientation(0.0, 0.0, 0.0))
    entity_appearance: int = 0
    dr_algorithm: int = 0
    dr_other_params: bytes = b"\x00" * 15
    dr_linear_accel: Vec3f = field(default_factory=lambda: Vec3f(0.0, 0.0, 0.0))
    dr_angular_vel: Vec3f = field(default_factory=lambda: Vec3f(0.0, 0.0, 0.0))
    marking_charset: int = 1
    marking: str = "ENTITY"
    capabilities: int = 0

    def pack(self) -> bytes:
        if self.timestamp == 0:
            self.timestamp = dis_timestamp_absolute()

        header = struct.pack(
            ">BBBBIHH",
            self.protocol_version & 0xFF,
            self.exercise_id & 0xFF,
            self.pdu_type & 0xFF,
            self.protocol_family & 0xFF,
            self.timestamp & 0xFFFFFFFF,
            self.length & 0xFFFF,
            0,
        )

        eid = struct.pack(">HHH", self.entity_id.site, self.entity_id.application, self.entity_id.entity)
        force_and_num = struct.pack(">BB", self.force_id, self.num_articulation_params)

        def pack_entity_type(et: EntityType) -> bytes:
            return struct.pack(
                ">BBHBBBB",
                et.kind, et.domain, et.country,
                et.category, et.subcategory, et.specific, et.extra
            )

        etype = pack_entity_type(self.entity_type)
        aetype = pack_entity_type(self.alt_entity_type)
        vel = struct.pack(">fff", self.linear_velocity.x, self.linear_velocity.y, self.linear_velocity.z)
        loc = struct.pack(">ddd", self.location.x, self.location.y, self.location.z)
        ori = struct.pack(">fff", self.orientation.psi, self.orientation.theta, self.orientation.phi)
        appearance = struct.pack(">I", self.entity_appearance)

        dr = (
            struct.pack(">B", self.dr_algorithm)
            + self.dr_other_params
            + struct.pack(">fff", self.dr_linear_accel.x, self.dr_linear_accel.y, self.dr_linear_accel.z)
            + struct.pack(">fff", self.dr_angular_vel.x, self.dr_angular_vel.y, self.dr_angular_vel.z)
        )

        mark11 = self.marking.encode("ascii", "ignore")[:11].ljust(11, b"\x00")
        marking = struct.pack(">B", self.marking_charset) + mark11
        caps = struct.pack(">I", self.capabilities)

        return header + eid + force_and_num + etype + aetype + vel + loc + ori + appearance + dr + marking + caps

    @staticmethod
    def unpack(data: bytes) -> "EntityStatePDU":
        if len(data) < 144:
            raise ValueError("Need 144 bytes")

        (ver, exid, pdu_type, fam, ts, length, _pad) = struct.unpack(">BBBBIHH", data[:12])
        offset = 12

        site, app, ent = struct.unpack(">HHH", data[offset:offset + 6])
        offset += 6
        force_id, num_art = struct.unpack(">BB", data[offset:offset + 2])
        offset += 2

        def unpack_entity_type(buf: bytes) -> EntityType:
            kind, domain, country, cat, subcat, spec, extra = struct.unpack(">BBHBBBB", buf)
            return EntityType(kind, domain, country, cat, subcat, spec, extra)

        et = unpack_entity_type(data[offset:offset + 8])
        offset += 8
        aet = unpack_entity_type(data[offset:offset + 8])
        offset += 8

        vx, vy, vz = struct.unpack(">fff", data[offset:offset + 12])
        offset += 12
        x, y, z = struct.unpack(">ddd", data[offset:offset + 24])
        offset += 24
        psi, theta, phi = struct.unpack(">fff", data[offset:offset + 12])
        offset += 12
        (appearance,) = struct.unpack(">I", data[offset:offset + 4])
        offset += 4

        (dr_alg,) = struct.unpack(">B", data[offset:offset + 1])
        offset += 1
        dr_other = data[offset:offset + 15]
        offset += 15
        ax, ay, az = struct.unpack(">fff", data[offset:offset + 12])
        offset += 12
        wx, wy, wz = struct.unpack(">fff", data[offset:offset + 12])
        offset += 12

        (charset,) = struct.unpack(">B", data[offset:offset + 1])
        offset += 1
        mark = data[offset:offset + 11].split(b"\x00", 1)[0].decode("ascii", "ignore")
        offset += 11
        (caps,) = struct.unpack(">I", data[offset:offset + 4])

        return EntityStatePDU(
            protocol_version=ver,
            exercise_id=exid,
            pdu_type=pdu_type,
            protocol_family=fam,
            timestamp=ts,
            length=length,
            entity_id=EntityID(site, app, ent),
            force_id=force_id,
            num_articulation_params=num_art,
            entity_type=et,
            alt_entity_type=aet,
            linear_velocity=Vec3f(vx, vy, vz),
            location=Vec3d(x, y, z),
            orientation=Orientation(psi, theta, phi),
            entity_appearance=appearance,
            dr_algorithm=dr_alg,
            dr_other_params=dr_other,
            dr_linear_accel=Vec3f(ax, ay, az),
            dr_angular_vel=Vec3f(wx, wy, wz),
            marking_charset=charset,
            marking=mark,
            capabilities=caps,
        )