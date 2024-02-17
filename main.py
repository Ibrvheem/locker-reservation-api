from datetime import datetime, timedelta
from fastapi import BackgroundTasks, FastAPI, HTTPException, Depends
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



class Profile(BaseModel):
    id: int
    old_password: Optional[str]
    new_password: Optional[str]
    phone: str


class Lockers(BaseModel):
    locker_id: str


class Reservation(BaseModel):
    locker_id: int
    user_id: int


class CreateReservation(BaseModel):
    locker_id: int


class ConfirmReservation(BaseModel):
    locker_id: int


class EndReservation(BaseModel):
    locker_id: int


# class ChangeReservation(BaseModel):
#     status: str
#     reservation_id: str


# remove this in production
@app.get("/users")
async def users():
    response = supabase.table("users").select("*").execute()
    user_data = response.data
    return user_data


@app.get("/lockers")
async def lockers():
    response = supabase.table("lockers").select("*").execute()
    user_data = response.data
    return user_data

@app.post("/lockers")
async def add_lockers(lockers: Lockers):

    try:
        response = (
            supabase.table("lockers")
            .insert(
                {
                    "locker_id": lockers.locker_id,
                }
            )
            .execute()
        )
        return response

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
      


@app.get("/reservations")
async def get_reservations():
    try:
        response = supabase.table("reservations").select("*, lockers(*)").execute()
        locker_codes = [locker for locker in response]
        return response

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/available_lockers")
async def available_lockers():
    try:
        response = supabase.from_("lockers").select("*", "reservations(*)").execute()
        # response = supabase.table("reservations").select("*").execute()
        # locker_codes = [locker for locker in response]
        return response

    except Exception as e:
        # return e
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/reservations/{user_id}")
async def get_user_reservations(user_id: int):
    try:
        response = supabase.table("reservations").select("*").eq("user_id", user_id).execute()
        return response.data

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



def generate_locker_id():
    locker_id = str(uuid.uuid4().hex)[:10]
    return locker_id


@app.post("/reservations/{user_id}")
async def add_reservation(reservation: Reservation, background_tasks: BackgroundTasks):
    unique_id = generate_locker_id()
    print(unique_id)

    try:
        response = (
            supabase.table("reservations")
            .insert(
                {
                    "locker_id": reservation.locker_id,
                    "reservation_id": unique_id,
                    "user_id": reservation.user_id,
                }
            )
            .execute()
        )
        background_tasks.add_task(delete_expired_reservations)
        return response

    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/reservations/{user_id}")
async def delete_reservation(reservation: Reservation):
    unique_id = generate_locker_id()
    print(unique_id)

    try:
        response = (
            supabase.table("reservations").delete().eq("locker_id", reservation.locker_id).execute()
        )
        return response

    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/create_reservation/{user_id}")
async def update_column(reservation: CreateReservation):
    unique_id = generate_locker_id()
    print(unique_id)
    
    try:
        response = supabase.from_('reservations').update({ 'reservation_id': unique_id, "status": "Reserved" }).eq('locker_id', reservation.locker_id).execute()

        if "error" in response:
            print(response)
            raise HTTPException(status_code=500, detail=reservation["error"])

        return {"reservation_id": unique_id, "message": "Column updated successfully"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/confirm_reservation")
async def update_column(reservation: ConfirmReservation):
    
    try:
        response = supabase.from_('reservations').update({  "status": "Ongoing" }).eq('locker_id', reservation.locker_id).execute()

        if "error" in response:
            print(response)
            raise HTTPException(status_code=500, detail=reservation["error"])

        return { "message": "Column updated successfully"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/end_reservation")
async def update_column(reservation: EndReservation):
    
    try:
        response = supabase.from_('reservations').update({  "status": "Pending" }).eq('locker_id', reservation.locker_id).execute()
        deleteReservation = supabase.from_('reservations').update({  "reservation_id": "" }).eq('locker_id', reservation.locker_id).execute()

        if "error" in response:
            print(response)
            raise HTTPException(status_code=500, detail=reservation["error"])

        return { "message": "Column updated successfully"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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


async def delete_expired_reservations():
    try:
        # Calculate the datetime 1 minute ago
        one_minute_ago = datetime.utcnow() - timedelta(seconds=20)
        
        # Query reservations that are older than 1 minute and have the "reserved" status
        response = supabase.table("reservations").delete().lt("created_at", one_minute_ago).eq("status", "reserved").execute()
        
        # Log the number of deleted reservations
        print(f"Deleted {response['count']} expired reservations")
    except Exception as e:
        print(f"Error deleting expired reservations: {e}")


@app.post("/delete_expired_reservations")
async def trigger_delete_expired_reservations(background_tasks: BackgroundTasks):
    # Add the delete_expired_reservations function to the background tasks
    background_tasks.add_task(delete_expired_reservations)
    return {"message": "Deleting expired reservations in the background"}
