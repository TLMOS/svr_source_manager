from fastapi import APIRouter, HTTPException

from app import crud, schemas, security
from app.dependencies import SessionDep

router = APIRouter(
    prefix="/users",
    tags=["User management"],
)


@router.post(
    "/create",
    response_model=schemas.User,
    summary="Create user",
    response_description="User created"
)
async def create(session: SessionDep,
                 user_schema: schemas.UserCreate):
    """
    Create user.

    Parameters:
    - **user**: user data
    """
    user = await crud.users.read_by_name(session, user_schema.name)
    if user is not None:
        raise HTTPException(status_code=400, detail="Username already exists")
    user_schema.password = security.get_password_hash(user_schema.password)
    user = await crud.users.create(session, user_schema)
    return user


@router.post(
    "/verify",
    response_model=schemas.User | None,
    summary="verify user credentials",
    response_description="User if credentials are valid"
)
async def verify(session: SessionDep,
                 name: str,
                 password: str):
    """
    verify user credentials.

    Parameters:
    - **name**: user name
    - **password**: user password
    """
    user = await crud.users.read_by_name(session, name)
    if user and security.verify_password(password, user.password):
        return user


@router.get(
    "/get/{id:int}",
    response_model=schemas.User,
    summary="Get user",
    response_description="User"
)
async def get(session: SessionDep,
              id: int):
    """
    Get user.

    Parameters:
    - **id**: user id
    """
    user = await crud.users.read(session, id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.get(
    "/get/all",
    response_model=list[schemas.User],
    summary="Get list of all users",
    response_description="List of all users"
)
async def get_all(session: SessionDep):
    """Get list of all users."""
    return await crud.users.read_all(session)


@router.delete(
    "/delete",
    response_model=schemas.User,
    summary="Delete user"
)
async def delete(session: SessionDep,
                 id: int):
    """
    Delete user.

    Parameters:
    - **id**: user id
    """
    user = await crud.users.read(session, id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return await crud.users.delete(session, id)
