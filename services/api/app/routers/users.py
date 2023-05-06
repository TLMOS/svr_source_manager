from fastapi import APIRouter, HTTPException

from app import crud, schemas, security
from app.security import RequiresAuthDep, RequiresAdminDep


router = APIRouter(
    prefix="/users",
    tags=["User management"],
)


@router.post(
    '/forget',
    summary="Logout",
)
async def forget(auth: RequiresAuthDep):
    """
    Logout.
    """
    user, _ = auth
    security.forget(user.name)


@router.post(
    "/create",
    response_model=schemas.User,
    summary="Create user",
    response_description="User created"
)
async def create(user_schema: schemas.UserCreate, session: RequiresAdminDep):
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


@router.get(
    "/me",
    response_model=schemas.User,
    summary="Get current user",
    response_description="User"
)
async def me(auth: RequiresAuthDep):
    """
    Get current user.
    """
    user, _ = auth
    return user


@router.get(
    "/get/{id:int}",
    response_model=schemas.User,
    summary="Get user",
    response_description="User"
)
async def get(id: int, session: RequiresAdminDep):
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
async def get_all(session: RequiresAdminDep):
    """Get list of all users."""
    return await crud.users.read_all(session)


@router.put(
    "/update/password",
    summary="Update user password"
)
async def update_password(password: str, auth: RequiresAuthDep):
    """
    Update user password.

    Parameters:
    - **id**: user id
    - **password**: new password
    """
    user, session = auth
    password = security.get_password_hash(password)
    await crud.users.update_password(session, user.id, password)


@router.put(
    "/update/max_sources",
    summary="Update user max sources",
)
async def update_max_sources(id: int, max_sources: int,
                             session: RequiresAdminDep):
    """
    Update user max sources.

    Parameters:
    - **id**: user id
    - **max_sources**: new max sources
    """
    user = await crud.users.read(session, id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    await crud.users.update_max_sources(session, id, max_sources)


@router.delete(
    "/delete",
    response_model=schemas.User,
    summary="Delete user"
)
async def delete(id: int, session: RequiresAdminDep):
    """
    Delete user.

    Parameters:
    - **id**: user id
    """
    user = await crud.users.read(session, id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return await crud.users.delete(session, id)
