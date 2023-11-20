from dataclasses import dataclass, asdict
from typing import Any, Dict
from customerrors import NotAValidInstance, NotAValidPostRequest


@dataclass
class BaseModel:
    def jsonify(self) -> Dict[str, Any]:
        return asdict(self)
