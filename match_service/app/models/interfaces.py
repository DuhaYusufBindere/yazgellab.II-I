from abc import ABC, abstractmethod
from typing import List, Optional
from .match import MatchCreate, MatchUpdate, MatchInDB

class BaseMatchRepository(ABC):
    """
    Match veritabanı işlemleri için Soyut Arayüz (Dependency Inversion Principle).
    Mocking ve farklı veritabanı motorlarına geçiş için esneklik sağlar.
    """
    
    @abstractmethod
    async def get_all(self) -> List[MatchInDB]:
        """Tüm maçları getirir."""
        pass

    @abstractmethod
    async def get_by_id(self, match_id: str) -> Optional[MatchInDB]:
        """Belirtilen ID'ye sahip maçı getirir."""
        pass

    @abstractmethod
    async def create(self, match: MatchCreate) -> MatchInDB:
        """Yeni bir maç kaydı oluşturur."""
        pass

    @abstractmethod
    async def update(self, match_id: str, update_data: MatchUpdate) -> Optional[MatchInDB]:
        """Belirtilen maçı günceller."""
        pass

    @abstractmethod
    async def delete(self, match_id: str) -> bool:
        """Belirtilen maçı siler."""
        pass
