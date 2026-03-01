import io
import os
from dataclasses import dataclass
from typing import Literal

from anyascii import anyascii
from datasets import load_dataset
from dotenv import load_dotenv
from faker import Faker
from google.cloud import storage
from PIL.Image import Image

load_dotenv()

bucket_name = os.environ.get("BUCKET_NAME")
client_storage = storage.Client()

faker = Faker(["pl_PL", "cs_CZ", "hu_HU"])

max_rows = 5000


@dataclass
class FaceImage:
    age: str
    gender: Literal["Male", "Female"]
    race: str
    imageData: Image
    name: str
    file_path: str


def handle_face_images():
    faceImages = dataset_to_face_images()
    load_into_gcp(faceImages)
    sql_str = map_to_insert_statement(faceImages)
    with open("insert_sql.sql", "w") as f:
        f.write(sql_str)


def dataset_to_face_images():
    ds = load_dataset("HuggingFaceM4/FairFace", "0.25")
    split = ds["train"]
    features = split.features

    rows: list[FaceImage] = []
    for i, row in enumerate(split):
        row_age = features["age"].int2str(row["age"])
        row_race = features["race"].int2str(row["race"])
        row_gender = features["gender"].int2str(row["gender"])
        file_path = f"{row_gender}/face_{i}_{row_race}_{row_age}"

        name = get_short_name("M" if row_gender == "Male" else "F")

        face = FaceImage(
            name=name,
            age=row_age,
            gender=row_gender,
            race=row_race,
            imageData=row["image"],
            file_path=file_path,
        )
        rows.append(face)
        if i >= max_rows:
            break
    return rows


def get_short_name(gender: Literal["M", "F"]) -> str:
    name = faker.name_male() if gender == "M" else faker.name_female()
    while len(name.split(" ")) != 2 or "-" in name:
        name = faker.name_male() if gender == "M" else faker.name_female()
    return anyascii(name).replace("'", "''")


def load_into_gcp(rows: list[FaceImage]):
    bucket = client_storage.bucket(bucket_name)

    for idx, r in enumerate(rows):
        buffer = io.BytesIO()
        r.imageData.save(buffer, format="JPEG")
        buffer.seek(0)

        blob = bucket.blob(r.file_path)
        blob.upload_from_file(buffer, content_type="image/jpeg")
        print("loaded bucket ", idx)


def map_to_insert_statement(faces: list[FaceImage]) -> str:
    start = (
        "DELETE FROM public.game_answer WHERE true;\n"
        "DELETE FROM public.game_session WHERE true;\n"
        "DELETE FROM public.face WHERE true;\n"
        "INSERT INTO public.face (file_path, name, gender, race) VALUES\n"
    )
    value_strings = [
        f"('{f.file_path}', '{f.name}', '{f.gender}', '{f.race}')" for f in faces
    ]
    return start + ",\n".join(value_strings)


if __name__ == "__main__":
    handle_face_images()
