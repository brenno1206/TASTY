import math
import json
import urllib.request
import urllib.parse
import ssl
from typing import Dict, Any, Tuple, Optional, List
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import select
from tasty.models import City, User, Business
from tasty.ext.db import db



def geocode_address(road: str, district: str, zipcode: str, city_name: str = "Vila Velha") -> Tuple[Optional[float], Optional[float]]:
    """
    Converte um endereço físico ou CEP em Latitude e Longitude.
    """
    query_string = ""
    try:
        clean_zip = zipcode.replace("-", "").strip() if zipcode else ""
        
        query_parts = []
        if road: query_parts.append(road)
        if district: query_parts.append(district)
        if city_name: query_parts.append(city_name)
        if clean_zip: query_parts.append(clean_zip)
        query_parts.append("Brasil")
        
        query_string = ", ".join(query_parts)
        encoded_query = urllib.parse.quote(query_string)
        
        url = f"https://nominatim.openstreetmap.org/search?q={encoded_query}&format=json&limit=1"
        
        req = urllib.request.Request(url, headers={'User-Agent': 'TastyAppBackend/1.0'})
        
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        
        with urllib.request.urlopen(req, timeout=5, context=ctx) as response:
            data = json.loads(response.read().decode())
            if data and len(data) > 0:
                return float(data[0]['lat']), float(data[0]['lon'])
                
    except Exception as e:
        print(f"Erro de rede ou limite na API Nominatim para '{query_string}': {e}")
        
    print("Aplicando coordenadas padrão de Vila Velha como contingência.")
    return -20.3222, -40.3381


def calculate_haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calcula a distância em quilômetros usando a fórmula de Haversine."""
    R = 6371.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2.0)**2 + \
        math.cos(phi1) * math.cos(phi2) * \
        math.sin(delta_lambda / 2.0)**2
        
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return round(R * c, 1)


def get_distance_between_user_and_business(user_id: int, business_id: int) -> Optional[float]:
    """Busca os endereços no DB e retorna a distância entre eles."""
    try:
        user = db.session.execute(select(User).where(User.id == user_id)).scalar_one_or_none()
        business = db.session.execute(select(Business).where(Business.id == business_id)).scalar_one_or_none()

        if not user or not user.addresses or not user.addresses[0].latitude:
            return None
            
        if not business or not business.addresses or not business.addresses[0].latitude:
            return None

        u_lat = float(user.addresses[0].latitude)
        u_lon = float(user.addresses[0].longitude)
        b_lat = float(business.addresses[0].latitude)
        b_lon = float(business.addresses[0].longitude)

        return calculate_haversine_distance(u_lat, u_lon, b_lat, b_lon)
        
    except (SQLAlchemyError, ValueError, TypeError):
        return None


def create_city(data: Dict[str, Any]) -> Tuple[bool, str, int]:
    """Cadastra uma nova cidade garantindo que não haja duplicatas geográficas."""
    if not data or not isinstance(data, dict):
        return False, "Dados inválidos.", 400
        
    name = data.get("name")
    state = data.get("state")
    country = data.get("country", "Brasil")
    
    if not name:
        return False, "O nome da cidade é obrigatório.", 400
        
    try:
        stmt = select(City).where(
            City.name.ilike(name),
            City.state.ilike(state) if state else City.state.is_(None),
            City.country.ilike(country) if country else City.country.is_(None)
        )
        
        if db.session.execute(stmt).scalar_one_or_none():
            return False, f"A cidade {name} - {state} já está cadastrada.", 400
            
        new_city = City(
            name=name,
            state=state,
            country=country,
            region=data.get("region")
        )
        
        db.session.add(new_city)
        db.session.commit()
        return True, "Cidade cadastrada com sucesso.", 201
        
    except SQLAlchemyError as e:
        db.session.rollback()
        return False, f"Erro interno do banco de dados: {str(e)}", 500


def get_city(city_id: int) -> Optional[City]:
    """Retorna os dados de uma cidade específica."""
    return db.session.execute(select(City).where(City.id == city_id)).scalar_one_or_none()


def update_city(city_id: int, data: Dict[str, Any]) -> Tuple[bool, str, int]:
    """Atualiza metadados da cidade."""
    city = get_city(city_id)
    if not city:
        return False, "Cidade não encontrada.", 404
        
    try:
        if "name" in data:
            city.name = data["name"]
        if "state" in data:
            city.state = data["state"]
        if "country" in data:
            city.country = data["country"]
        if "region" in data:
            city.region = data["region"]
            
        db.session.commit()
        return True, "Cidade actualizada com sucesso.", 200
        
    except SQLAlchemyError as e:
        db.session.rollback()
        return False, f"Erro ao atualizar cidade: {str(e)}", 500


def get_all_cities() -> List[City]:
    """Lista todas as cidades (útil para dropdowns de filtros)."""
    stmt = select(City).order_by(City.state, City.name)
    return list(db.session.execute(stmt).scalars().all())
