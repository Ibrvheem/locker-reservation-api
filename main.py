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
    response = supabase.table('lockers').select("*").execute()
    user_data = response.data
    return user_data


@app.post("/create_user")
async def create_user(user: User):
    # print(user)
    # converted_data = {}
    # for key, value in user.items():
    #     if value is not None:
    #         converted_data[key] = value
    #     else:
    #         converted_data[key] = {'value': None, 'isValid': False, 'errorText': f'{key.capitalize()} is required'}

    #     print(converted_data)
    # for col in user:
        # if "value" in col[1]:
        # print(col[1]["value"])
    # user_data = [{col} for col in user]
    # print(user_data)
    try:
        user_data = user.model_dump()
        print(user_data)
        response =  supabase.table('users').insert(user_data).execute()
        print(response)
        if "error" in response:
            print(response)
            raise HTTPException(status_code=500, detail=user["error"])
        return {"message": "user created successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    
    
@app.post("/login")
async def login(user: UserLogin):
    try:
        user_login_data = user.model_dump()
        print(user_login_data)
        response = supabase.table("users").select("regNo", "password").match(user_login_data).execute()

        # if "data" in response.model_dump() and response.model_dump()["data"] is not None:
        response_data = response.data
        print(len(response_data))
        if len(response_data) == 1:
            if user_login_data == response_data[0] :
                return {"message": "User logged in successfully"}
            
        raise HTTPException(status_code=401, detail="Invalid registration number or password")
    
    except HTTPException as http_err:
        raise http_err
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/admin_login")
async def admin_login(user: AdminLogin):
    try:
        user_login_data = user.model_dump()
        print(user_login_data)
        response = supabase.table("admin_users").select("staffId", "password").match(user_login_data).execute()

        # if "data" in response.model_dump() and response.model_dump()["data"] is not None:
        response_data = response.data
        print(len(response_data))
        if len(response_data) == 1:
            if user_login_data == response_data[0] :
                return {"message": "Admin logged in successfully"}
            
        raise HTTPException(status_code=401, detail="Invalid staff Id or password")
    
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


@app.get("/lockers")
async def lockers():
    try:
        response = supabase.table('lockers').select("*").execute()
        locker_codes = [locker for locker in response]
        return locker_codes
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    


