import logging
from typing import Any

from fastapi import FastAPI, HTTPException, Request, status, Body
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from bson import ObjectId
from bson.errors import InvalidId

from database import students_collection
from models import StudentCreate


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Students API")


def student_serializer(student: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": str(student["_id"]),
        "name": student["name"],
        "email": student["email"],
        "age": student["age"],
    }


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError
) -> JSONResponse:
    logger.warning("Error de validación en %s: %s", request.url.path, exc.errors())
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "detail": "Bad Request",
            "errors": exc.errors()
        },
    )


@app.get("/")
def root() -> dict[str, str]:
    logger.info("Acceso al endpoint raíz")
    return {"message": "API de estudiantes funcionando correctamente"}


@app.get("/students")
def get_students() -> list[dict[str, Any]]:
    logger.info("Listando todos los estudiantes")
    students = students_collection.find()
    return [student_serializer(student) for student in students]


@app.get("/students/{student_id}")
def get_student(student_id: str) -> dict[str, Any]:
    logger.info("Buscando estudiante con id=%s", student_id)

    try:
        student = students_collection.find_one({"_id": ObjectId(student_id)})
    except InvalidId:
        logger.warning("ID inválido recibido: %s", student_id)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID inválido"
        )

    if not student:
        logger.warning("Estudiante no encontrado: %s", student_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Entidad no encontrada"
        )

    return student_serializer(student)


@app.post("/students", status_code=status.HTTP_201_CREATED)
def create_student(student: StudentCreate) -> dict[str, Any]:
    logger.info("Creando estudiante con email=%s", student.email)

    student_dict = student.model_dump()
    result = students_collection.insert_one(student_dict)

    created_student = students_collection.find_one({"_id": result.inserted_id})

    logger.info("Estudiante creado con id=%s", result.inserted_id)
    return student_serializer(created_student)


@app.delete("/students/{student_id}")
def delete_student(student_id: str) -> dict[str, str]:
    logger.info("Eliminando estudiante con id=%s", student_id)

    try:
        result = students_collection.delete_one({"_id": ObjectId(student_id)})
    except InvalidId:
        logger.warning("ID inválido recibido al borrar: %s", student_id)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID inválido"
        )

    if result.deleted_count == 0:
        logger.warning("No se encontró estudiante para borrar: %s", student_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Entidad no encontrada"
        )

    logger.info("Estudiante eliminado correctamente: %s", student_id)
    return {"message": "Entidad eliminada correctamente"}


@app.put("/students/{student_id}")
def update_student_age(student_id: str, age: int = Body(..., ge=0)) -> dict[str, Any]:
    logger.info("Actualizando edad del estudiante id=%s", student_id)

    try:
        result = students_collection.update_one(
            {"_id": ObjectId(student_id)},
            {"$set": {"age": age}}
        )
    except InvalidId:
        logger.warning("ID inválido recibido al actualizar: %s", student_id)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID inválido"
        )

    if result.matched_count == 0:
        logger.warning("Estudiante no encontrado para actualizar: %s", student_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Entidad no encontrada"
        )

    updated_student = students_collection.find_one({"_id": ObjectId(student_id)})

    logger.info("Edad actualizada correctamente para id=%s", student_id)
    return student_serializer(updated_student)