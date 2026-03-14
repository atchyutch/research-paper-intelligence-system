from typing import List
from uuid import uuid4

from botocore.exceptions import ClientError
from fastapi import APIRouter, UploadFile, File, Header, Depends ,HTTPException, status
import fitz
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from backend.app.api.deps import get_db
from backend.app.api.v1.endpoints.auth import get_current_user
import boto3

from backend.app.core.config import settings
from backend.app.db.base import Documents
from backend.app.rag.schemas.document_schemas import DocumentResponse

document_router = APIRouter(prefix="/documents")

@document_router.post("/multiple/upload")
async def multiple_upload_documents(files: List[UploadFile] = File(),
                                    current_user = Depends(get_current_user), db=Depends(get_db)):
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")

    results = [] #The one big list for the project
    for file in files:
        try:
            data = await file.read()
            await file.close()

            validate_file_type(file)

            # Extract stuff from the pdf
            pdf_doc = fitz.open(stream=data, filetype="pdf")
            page_count = pdf_doc.page_count
            meta = pdf_doc.metadata or {}
            pdf_doc.close()

            # Generate a safe r2_key for each document for us to access in the future
            doc_uuid = str(uuid4())
            r2_key = f"document/{current_user.user_id}/{doc_uuid}"

            # Upload to R2
            client = get_r2_client(settings.R2_AWS_S3_ENDPOINT, settings.R2_ACCESS_TOKEN, settings.R2_SECRET_ACCESS_KEY)
            try:
                client.put_object(Bucket=settings.R2_BUCKET_NAME,
                                  Key=r2_key,
                                  Body=data,
                                  metadata=meta)
            except ClientError as e:
                raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE, detail=str(e))

            new_doc = Documents(
                user_id=current_user.user_id,
                file_name=file.filename,
                document_link=r2_key,
                page_count=page_count,
                size_bytes=len(data)
            )

            db.add(new_doc)
            db.commit()
            db.refresh(new_doc)
            results.append({
                "filename": new_doc.file_name,
                "status": True
            })
        except HTTPException as e:
                db.rollback()
                results.append({
                    "filename": getattr(file, "filename", None),
                    "status": "Failed",
                    "Reason" : str(e)
                })
                raise HTTPException(status_code=500, detail="Failed to store document metadata")
        except IntegrityError as e:
            db.rollback()
            results.append({
                "filename": getattr(file, "filename", None),
                "status": "Failed",
                "Reason": str(e)
            })
            raise HTTPException(status_code=500, detail="Failed to store the document details, could be a "
                                                        "constraint issue")
    return results


def validate_file_type(file: UploadFile=File(...)):
    if file.content_type not in ("application/pdf", "application/octet-stream"):
        raise HTTPException(status_code = status.HTTP_406_NOT_ACCEPTABLE,
                        detail="File type not supported, kindly upload a pdf.")
    if not (file.filename).endswith(".pdf"):
        raise HTTPException(status_code = status.HTTP_406_NOT_ACCEPTABLE, detail="File has be of pdf extension.")
    return True


def get_r2_client(r2_endpoint:  str, access_key:str, secret_key:str):
    try:
        client_retrieved = boto3.client(
            "s3",
            endpoint_url = r2_endpoint,
            aws_access_key_id = access_key,
            aws_secret_access_key = secret_key,
            region_name = "us-east-1"
        )
    except ClientError as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail = str(e))

    return client_retrieved

@document_router.get("/")
def get_documents(user=Depends(get_current_user), db=Depends(get_db)):
    try:
        docs = db.query(Documents).filter(Documents.user_id == user.user_id).all()
        return docs
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except HTTPException as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="HTTP error for deleting the conversations")


@document_router.get("/{doc_id}")
def get_single_document(doc_id, user=Depends(get_current_user), db=Depends(get_db)) -> DocumentResponse:
    """
    Return a single document by ID
    :param doc_id: Document ID
    :param user: Current user
    :param db: Session connection to database
    :return: Document Response with relevant data
    """
    try:
        doc = db.Query(Documents).filter(Documents.document_id == doc_id,
                                   Documents.user_id == user.user_id ).one()
        docResponse = DocumentResponse(
            document_id=doc.document_id,
            user_id = doc.user_id,
            created_at = doc.created_at,
            file_name = doc.file_name,
            page_count = doc.page_count
        )
        return docResponse
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except HTTPException as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@document_router.post("/delete/{doc_id}")
def delete_single_doc(doc_id, user=Depends(get_current_user), db=Depends(get_db)):
    pass
    #TODO
    # Delete from R2 and Pinecone
