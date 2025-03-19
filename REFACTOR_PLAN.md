# Refactoring Plan for Core Modules

## Phase 1: API Standardization & Infrastructure Improvement
```mermaid
graph TD
    A[API Utility Layer] --> B[Database Pooling]
    A --> C[Error Framework]
    A --> D[Logging Middleware]
    B --> E[SQLAlchemy Integration]
    C --> F[Custom Exceptions]
    D --> G[Structured Logs]
```

**Implementation Steps**:
1. Create `src/core/infrastructure/database.py` with connection pooling
2. Add `src/core/utils/error_handling.py` with retry decorators
3. Implement Prometheus metrics in `src/core/monitoring/`

## Phase 2: Code Restructuring
```mermaid
classDiagram
    class BaseBookingRequest
    class CarRentalRequest
    class HotelBookingRequest
    
    BaseBookingRequest <|-- CarRentalRequest
    BaseBookingRequest <|-- HotelBookingRequest
```

**Key Changes**:
- Consolidate 4 booking models into 1 base class
- Move business logic to `src/core/services/`
- Add async support with `anyio`

## Phase 3: Testing & Monitoring
**Test Coverage Plan**:
| Component       | Current | Target |
|-----------------|---------|--------|
| API Endpoints   | 0%      | 90%    |
| Database Layer  | 20%     | 100%   |
| Error Handling  | 10%     | 100%   |

**Monitoring Metrics**:
- API latency (95th percentile)
- Error rate by type
- Database connection pool usage

## Implementation Timeline
```mermaid
gantt
    title 2-Week Implementation Plan
    dateFormat  YYYY-MM-DD
    section Core
    Database Pooling   :active, 2025-03-19, 2d
    Error Handling     :2025-03-21, 3d
    Base Models        :2025-03-24, 2d

    section Tests
    Integration Tests :2025-03-26, 4d
    Load Tests         :2025-03-31, 2d
```

## Code Samples
```python
# src/core/infrastructure/database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

engine = create_engine(
    "sqlite:///travel2.sqlite",
    pool_size=10,
    max_overflow=20,
    pool_recycle=3600
)

SessionLocal = sessionmaker(bind=engine)
```

```python
# src/core/utils/error_handling.py
from tenacity import retry, stop_after_attempt, wait_exponential

def db_retry(func):
    return retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, max=10),
        reraise=True
    )(func)