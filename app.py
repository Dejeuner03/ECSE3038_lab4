from fastapi import FastAPI, Response, HTTPException
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, BeforeValidator, Field
from datetime import datetime
import motor.motor_asyncio
from fastapi.middleware.cors import CORSMiddleware
from typing import Annotated, List

app = FastAPI()

origins = [ "https://ecse3038-lab3-tester.netlify.app" ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

connection = motor.motor_asyncio.AsyncIOMotorClient("mongodb+srv://heavenlyflower2020:Dejeuner_2103@cluster0.3lokw.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
tank_db = connection.watertanks
profile_db = connection.info

PyObjectId = Annotated[str, BeforeValidator(str)]

class Profile(BaseModel):
    id: PyObjectId = Field(default= None,alias="_id")
    
    username: str
    color: str
    role: str
    last_updated: datetime = datetime.now()

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

@app.post("/profile")
async def create_profile(profile_request: Profile):
    profile_dictionary = profile_request.model_dump()
    created_profile = await profile_db["Files"].insert_one(profile_dictionary)
    profile = await profile_db["Files"].find_one({"_id": created_profile.inserted_id})
    return Profile(**profile)

@app.get("/profile")
async def get_profile():
    profile_collection = await profile_db["Files"].find().to_list(1000)
    return ProfileCollection(profiles = profile_collection)

@app.get("/tank")
async def get_tank():
    tank_collection = await tank_db["tanks"].find().to_list(1000)
    return TankCollection(tanks = tank_collection)

@app.post("/tank")
async def create_tank(tank_request: Tank):
    tank_dictionary= tank_request.model_dump()
    created_tank= await tank_db["tanks"].insert_one(tank_dictionary)
    tank = await tank_db["tanks"].find_one({"_id": created_tank.inserted_id})
    return Tank(**tank)
  
@app.delete("/tank/{id}")
async def delete_tank(id: str):
    tank = await tank_db["tanks"].find_one({"_id": PyObjectId(id)})
    print(f"Tank found: {tank}")
    if not tank:
        raise HTTPException(status_code=404, detail="tank is not here")
    
    deleted_tank = await tank_db["tanks"].delete_one({"_id": PyObjectId(id)})
    if deleted_tank.deleted_count == 1:
        return Response (status_code= 204)
    else:
        HTTPException(status_code= 404, detail="Tank not found")
    
@app.patch("/tank/{id}")
async def update_tank(id: str, tank_update:TankUpdate):
    tank = await tank_db["tanks"].find_one({"_id":PyObjectId(id)})
    if not tank:  
        raise HTTPException(status_code= 404, detail="Tank not found")
    update_data = tank_update.model_dump(exclude_unset=True)
    await tank_db["tanks"].update_one({"_id": PyObjectId(id)},{set: update_data})
    updated_tank = await tank_db["tanks"].find_one({"_id": PyObjectId(id)})
    return Tank(**updated_tank)