from fastapi import FastAPI, Response, HTTPException
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, BeforeValidator, Field
from datetime import datetime
import motor.motor_asyncio
from fastapi.middleware.cors import CORSMiddleware
from typing import Annotated, List
from dotenv import load_dotenv
import os
from bson import ObjectId

load_dotenv ()

app = FastAPI()


connection = motor.motor_asyncio.AsyncIOMotorClient(os.getenv("My_Key"))
tank_db = connection.watertanks
profile_db = connection.info

origins = [ "https://ecse3038-lab3-tester.netlify.app" ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



PyObjectId = Annotated[str, BeforeValidator(str)]

class Profile(BaseModel):
    id: PyObjectId = Field(default= None,alias="_id")
    
    username: str
    color: str
    role: str
    last_updated: datetime = Field(default_factory=datetime.now)

class Tank(BaseModel):
     id: PyObjectId = Field(default= None,alias="_id")
     location:str
     lat: float
     long:float

class TankUpdate(BaseModel):
    
     location:str| None = None 
     lat: float | None = None
     long:float | None = None 

class TankCollection(BaseModel):
    tanks: List[Tank]
    
class ProfileCollection(BaseModel):
    profiles: List[Profile]
    
async def update_profile():
    profile = await profile_db["Files"].find_one({})
    if profile is None:
            raise ValueError("No profile found in the database")
    profile_object = Profile(**profile)
    profile_object.last_updated = datetime.now()
    profile_dict =  profile_object.model_dump()
    profile_db["Files"].find_one_and_update({"_id": ObjectId(profile["_id"])},{"$set":profile_dict})

@app.post("/profile",status_code= 201)
async def create_profile(profile_request: Profile):
    profile_dictionary = profile_request.model_dump(exclude="id")
    created_profile = await profile_db["Files"].insert_one(profile_dictionary)
    profile = await profile_db["Files"].find_one({"_id": created_profile.inserted_id})
    if profile is None:
        raise HTTPException(400)
    return Profile(**profile)

@app.get("/profile")
async def get_profile():
    profile_collection = await profile_db["Files"].find().to_list(1)
    if len(profile_collection)== 0:
        return []
    return ProfileCollection(profiles = profile_collection)

@app.get("/tank")
async def get_tank():
    tank_collection = await tank_db["tanks"].find().to_list(1000)
    if len(tank_collection) == 0:
        return []
    return TankCollection(tanks = tank_collection).tanks

@app.post("/tank")
async def create_tank(tank_request: Tank):
    tank_dictionary= tank_request.model_dump(exclude="id")
    created_tank= await tank_db["tanks"].insert_one(tank_dictionary)
    tank = await tank_db["tanks"].find_one({"_id": created_tank.inserted_id})
    if tank is None:
        raise HTTPException(400)
    await update_profile()
    return Tank(**tank)
  
@app.delete("/tank/{id}")
async def delete_tank(id: str):
    tank_deletion = await tank_db["tanks"].delete_one({"_id": ObjectId(id)})
    if tank_deletion.deleted_count == 1:
        await update_profile()
        return Response(status_code= 204)
    raise HTTPException(status_code= 404, detail=f"Tank {id} not found")
    
@app.patch("/tank/{id}")
async def update_tank(id: str, tank_update_request:TankUpdate):
    update_tank_dict = tank_update_request.model_dump(exclude_unset= True)
    updated_tank = await tank_db["tanks"].find_one_and_update({"_id":ObjectId(id)}, {"$set": update_tank_dict}, return_document=True)
    print(updated_tank)
    if updated_tank is None:  
        raise HTTPException(status_code= 404, detail="Tank not found")
    await update_profile()
    return Tank(**updated_tank)