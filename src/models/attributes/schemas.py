from flask_sqlalchemy.session import Session
from marshmallow import fields
from sqlalchemy.orm.scoping import scoped_session

from ...database import db, ma
from .models import Attribute


class AttributesSchema(ma.SQLAlchemyAutoSchema):
    metadata_id = fields.String()

    class Meta:
        model = Attribute
        load_instance = True
        sqla_session: scoped_session[Session] = db.session


attribute_schema = AttributesSchema()
attributes_schema = AttributesSchema(many=True)
Attribute.set_schemas(attribute_schema, attributes_schema)
