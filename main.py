from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Annotated, Optional
from dotenv import load_dotenv
import os
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


@app.get("/users")
async def users():
    response = supabase.table('users').select("*").execute()
    user_data = response.data
    return user_data


@app.get("/lockers")
async def lockers():
    response = supabase.table('lockers').select("*").single.execute()
    user_data = response.data
    return user_data


@app.get("/reservations")
async def lockers():
    try:
        response = supabase.table('reservations').select("*, lockers(*)").execute()
        locker_codes = [locker for locker in response]
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    


@app.post("/create_user")
async def create_user(user: User):
    try:
        user_data = user.model_dump()
        print(user_data)
        response =  supabase.table('users').insert(user_data).execute()
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
        response = supabase.table("users").select("id, fullname, email, regNo, phone").eq("regNo", user_login_data["regNo"]).eq("password", user_login_data["password"]).execute()
        if len(response.data) == 1:   
                return response.data[0]
        else:
            print(response.data)
            print(len(response.data))
            raise HTTPException(status_code=401, detail="Invalid registration number or password")
    
    except HTTPException as http_err:
        raise http_err
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/admin_login")
async def admin_login(user: AdminLogin):
    try:
        admin_login_data = user.model_dump()
        response = supabase.table("admin_users").select("id, fullname, email, staffId, phone").eq("staffId", admin_login_data["staffId"]).eq("password", admin_login_data["password"]).execute()
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
async def editProfie():
    try:
        response = supabase.table('users').update({'password': 'Austrailia'}).eq('id', 1).execute()
        
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))




