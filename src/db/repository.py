from typing import Any, Generic, List, Optional, Type, TypeVar
from sqlmodel import SQLModel, Session, select

# Define ModelType as a TypeVar that is a subclass of SQLModel
ModelType = TypeVar("ModelType", bound=SQLModel)
CreateSchemaType = TypeVar("CreateSchemaType", bound=SQLModel) # For creating new records
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=SQLModel) # For updating records

class BaseRepository(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, model: Type[ModelType]):
        """
        Base class for CRUD operations.
        `model`: A SQLModel class
        """
        self.model = model

    def create(self, db_session: Session, *, obj_in: CreateSchemaType) -> ModelType:
        # Ensure obj_in is a dict if needed by model_validate, or directly pass if it's a Pydantic model
        # For SQLModel, it expects a Pydantic model or a dict.
        # If CreateSchemaType is a Pydantic model (which it should be, bound by SQLModel),
        # this should work directly.
        db_obj = self.model.model_validate(obj_in) # Use model_validate for Pydantic v2 compatibility
        db_session.add(db_obj)
        db_session.commit()
        db_session.refresh(db_obj)
        return db_obj

    def get(self, db_session: Session, id: Any) -> Optional[ModelType]:
        # Assuming 'id' is the primary key attribute name.
        # For SQLModel, if the primary key is named 'id', this is fine.
        # If it can be other names, this might need adjustment or configuration.
        statement = select(self.model).where(self.model.id == id)
        return db_session.exec(statement).first()

    def get_multi(
        self, db_session: Session, *, skip: int = 0, limit: int = 100
    ) -> List[ModelType]:
        statement = select(self.model).offset(skip).limit(limit)
        return db_session.exec(statement).all()

    def update(
        self, db_session: Session, *, db_obj: ModelType, obj_in: UpdateSchemaType
    ) -> ModelType:
        # obj_in is expected to be a Pydantic model (UpdateSchemaType)
        # model_dump() converts it to a dict. exclude_unset=True means only fields explicitly set in obj_in are included.
        obj_data = obj_in.model_dump(exclude_unset=True) # Use model_dump for Pydantic v2
        for field, value in obj_data.items():
            setattr(db_obj, field, value)
        db_session.add(db_obj)
        db_session.commit()
        db_session.refresh(db_obj)
        return db_obj

    def remove(self, db_session: Session, *, id: Any) -> Optional[ModelType]:
        # db_session.get() is a convenient way to fetch by primary key.
        obj = db_session.get(self.model, id)
        if obj:
            db_session.delete(obj)
            db_session.commit()
        return obj
