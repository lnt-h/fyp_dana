"""PostGIS column types without a GeoAlchemy2 dependency.

Values cross the boundary as EWKT text, e.g. ``"SRID=4326;POINT(108.2208 16.0544)"``
(longitude first).
Writes go through ``ST_GeogFromText``; reads come back through ``ST_AsEWKT``.
"""

from typing import Any

from sqlalchemy import Text, func
from sqlalchemy.sql.elements import ColumnElement
from sqlalchemy.types import UserDefinedType


class Geography(UserDefinedType[str]):
    cache_ok = True

    def __init__(self, geometry_type: str = "Point", srid: int = 4326) -> None:
        self.geometry_type = geometry_type
        self.srid = srid

    def get_col_spec(self, **kw: Any) -> str:
        return f"geography({self.geometry_type},{self.srid})"

    def bind_expression(self, bindvalue: Any) -> ColumnElement[str]:
        return func.ST_GeogFromText(bindvalue, type_=Text)

    def column_expression(self, colexpr: Any) -> ColumnElement[str]:
        return func.ST_AsEWKT(colexpr, type_=Text)


def ewkt_point(lng: float, lat: float, srid: int = 4326) -> str:
    """EWKT for a geography point; PostGIS axis order is longitude, latitude."""
    return f"SRID={srid};POINT({lng} {lat})"
