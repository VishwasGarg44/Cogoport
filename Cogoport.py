from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from typing import Optional

# Database Setup
Base = declarative_base()

class CountryConfig(Base):
    __tablename__ = "country_config"

    id = Column(Integer, primary_key=True, index=True)
    country_code = Column(String(2), unique=True, nullable=False)
    business_name = Column(String(255))
    # Add additional fields specific to each country (e.g., PAN, GSTIN for India)

# Dependency for Database Session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

engine = create_engine(f"postgresql://user:password@host:port/database")  # Replace with your credentials
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Pydantic Schemas
class CreateConfig(BaseModel):
    country_code: str
    business_name: str
    # Add fields for additional country-specific data

class Config(BaseModel):
    id: int
    country_code: str
    business_name: str
    # Include additional fields from CountryConfig model

class UpdateConfig(BaseModel):
    business_name: Optional[str]
    # Include fields for updating additional country-specific data


# FastAPI Application
app = FastAPI()
app.dependency_injector = get_db  # Inject dependency into all endpoints


# CRUD Operations as Endpoints

# Create Configuration
@app.post("/create_configuration", response_model=Config)
def create_configuration(config: CreateConfig, db: Session = Depends(get_db)):
    new_config = CountryConfig(**config.dict())  # Unpack data from CreateConfig
    try:
        db.add(new_config)
        db.commit()
        db.refresh(new_config)
        return new_config
    except IntegrityError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


# Get Configuration
@app.get("/get_configuration/{country_code}", response_model=Config)
def get_configuration(country_code: str, db: Session = Depends(get_db)):
    config = db.query(CountryConfig).filter(CountryConfig.country_code == country_code).first()
    if not config:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Country {country_code} not found")
    return config


# Update Configuration
@app.post("/update_configuration/{country_code}", response_model=Config)
def update_configuration(country_code: str, update_data: UpdateConfig, db: Session = Depends(get_db)):
    config = db.query(CountryConfig).filter(CountryConfig.country_code == country_code).first()
    if not config:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Country {country_code} not found")
    for field, value in update_data.dict(exclude_unset=True).items():
        setattr(config, field, value)
    db.commit()
    db.refresh(config)
    return config


