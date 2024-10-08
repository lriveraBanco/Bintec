from bson import ObjectId
from fastapi import APIRouter, status, Response, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from passlib.hash import sha256_crypt
from starlette.status import HTTP_204_NO_CONTENT
from jose import JWTError
from datetime import timedelta
from app.models.user import User
from app.config.db import conn
from app.schemas.user import userEntity, usersEntity
from app.utils.auth import create_access_token, verify_token
from app.models.__init__ import UserResponse, UserPasswordUpdate

user = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

@user.post("/login", tags=["auth"])
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = conn.local.user.find_one({"email": form_data.username.lower()})  # Asegúrate de que sea minúscula
    if not user or not sha256_crypt.verify(form_data.password, user["password"]):
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(data={"sub": user["email"]}, expires_delta=access_token_expires)
    return {"access_token": access_token, "token_type": "bearer"}


@user.get('/profile', response_model=UserResponse, tags=["auth"]) 
async def get_profile(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    # Verify the token and extract email
    email = verify_token(token, credentials_exception)
    # Fetch the user by email
    user = conn.local.user.find_one({"email": email})
    if user is None:
        raise credentials_exception
    # Remove the password from the response
    user_data = userEntity(user)
    user_data.pop("password", None)  # Remove password before returning
    return user_data

@user.put('/profile/change-password', tags=["auth"])
async def change_password(password_data: UserPasswordUpdate, token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    # Verify token and get the email
    email = verify_token(token, credentials_exception)
    # Fetch the user from the database
    user = conn.local.user.find_one({"email": email})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    # Verify the current password
    if not sha256_crypt.verify(password_data.current_password, user["password"]):
        raise HTTPException(status_code=400, detail="Incorrect current password")
    # Hash and update the new password
    hashed_new_password = sha256_crypt.hash(password_data.new_password)
    conn.local.user.update_one({"email": email}, {"$set": {"password": hashed_new_password}})
    return {"msg": "Password updated successfully"}




@user.get('/users', response_model=list[User], tags=["users"])
async def find_all_users():
    # print(list(conn.local.user.find()))
    return usersEntity(conn.local.user.find())


@user.post('/users', response_model=User, tags=["users"])
async def create_user(user: User):
    new_user = dict(user)
    new_user["password"] = sha256_crypt.hash(new_user["password"])
    del new_user["id"]
    id = conn.local.user.insert_one(new_user).inserted_id
    user = conn.local.user.find_one({"_id": id})
    return userEntity(user)


@user.get('/users/{id}', response_model=User, tags=["users"])
async def find_user(id: str):
    return userEntity(conn.local.user.find_one({"_id": ObjectId(id)}))


@user.put("/users/{id}", response_model=User, tags=["users"])
async def update_user(id: str, user: User):
    conn.local.user.find_one_and_update({
        "_id": ObjectId(id)
    }, {
        "$set": dict(user)
    })
    return userEntity(conn.local.user.find_one({"_id": ObjectId(id)}))


@user.delete("/users/{id}", status_code=status.HTTP_204_NO_CONTENT, tags=["users"])
async def delete_user(id: str):
    conn.local.user.find_one_and_delete({
        "_id": ObjectId(id)
    })
    return Response(status_code=HTTP_204_NO_CONTENT)
