from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Annotated, Optional
from dotenv import load_dotenv
import os
import uuid
from supabase import create_client, Client

load_dotenv()

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class User(BaseModel):
    fullname: str
    regNo: str
    password: str
    phone: Optional[str] = None
    email: str


class UserLogin(BaseModel):
    regNo: str
    password: str


class AdminLogin(BaseModel):
    staffId: str
    password: str


class EditProfile(BaseModel):
    password: str
    phone: str


class Lockers(BaseModel):
    code: str


class Reservation(BaseModel):
    locker_id: int
    user_id: int


# remove this in production
@app.get("/users")
async def users():
    response = supabase.table("users").select("*").execute()
    user_data = response.data
    return user_data


@app.get("/lockers")
async def lockers():
    response = supabase.table("lockers").select("*").single.execute()
    user_data = response.data
    return user_data


@app.get("/reservations")
async def get_reservations():
    try:
        response = supabase.table("reservations").select("*, lockers(*)").execute()
        locker_codes = [locker for locker in response]
        return response

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def generate_locker_id():
    locker_id = str(uuid.uuid4().hex)[:10]
    return locker_id


@app.post("/reservations")
async def add_reservation(reservation: Reservation):
    unique_id = generate_locker_id()
    print(unique_id)

    try:
        response = (
            supabase.table("users")
            .insert(
                {
                    "locker_id": reservation.locker_id,
                    "reservation_id": unique_id,
                    "user_id": reservation.user_id,
                }
            )
            .execute()
        )
        return response

    except Exception as e:
        print(e)
        return e


@app.post("/create_user")
async def create_user(user: User):
    try:
        user_data = user.model_dump()
        print(user_data)
        response = supabase.table("users").insert(user_data).execute()
        print(response)
        if "error" in response:
            print(response)
            raise HTTPException(status_code=500, detail=user["error"])
        return response.data[0]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/login")
async def login(user: UserLogin):
    try:
        user_login_data = user.model_dump()
        # print(user_login_data)
        response = (
            supabase.table("users")
            .select("id, fullname, email, regNo, phone")
            .eq("regNo", user_login_data["regNo"])
            .eq("password", user_login_data["password"])
            .execute()
        )
        if len(response.data) == 1:
            return response.data[0]
        else:
            print(response.data)
            print(len(response.data))
            raise HTTPException(
                status_code=401, detail="Invalid registration number or password"
            )

    except HTTPException as http_err:
        raise http_err

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/admin_login")
async def admin_login(user: AdminLogin):
    try:
        admin_login_data = user.model_dump()
        response = (
            supabase.table("admin_users")
            .select("id, fullname, email, staffId, phone")
            .eq("staffId", admin_login_data["staffId"])
            .eq("password", admin_login_data["password"])
            .execute()
        )
        if len(response.data) == 1:
            return response.data[0]
        else:
            print(response.data)
            print(len(response.data))
            raise HTTPException(status_code=401, detail="Invalid staff id or password")

    except HTTPException as http_err:
        raise http_err

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class Profile(BaseModel):
    id: int
    old_password: Optional[str]
    new_password: Optional[str]
    phone: str


@app.patch("/edit")
async def editProfie(profile: Profile):
    print(profile)
    try:
        if profile.old_password:
            response = (
                supabase.table("users")
                .update({"password": profile.new_password, "phone": profile.phone})
                .eq("id", profile.id)
                .eq("password", profile.old_password)
                .execute()
            )
        else:
            response = (
                supabase.table("users")
                .update({"password": profile.new_password, "phone": profile.phone})
                .eq("id", profile.id)
                .execute()
            )
        return {"message": "succesfully updated profile"}
    except Exception as e:
        print(e)
        return e
