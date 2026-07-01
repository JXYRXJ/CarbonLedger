import threading
from typing import Dict, Any


class MetricsService:
    """
    In-memory Metrics Service tracking latencies, transaction volumes,
    error counts, database queries, and cache performance metrics.
    """
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._total_requests = 0
        self._total_response_time = 0.0
        self._error_count = 0
        
        self._auth_attempts = 0
        self._marketplace_txs = 0
        self._retirement_ops = 0
        self._db_queries = 0
        
        self._cache_hits = 0
        self._cache_misses = 0

    def record_request(self, duration_sec: float, status_code: int) -> None:
        with self._lock:
            self._total_requests += 1
            self._total_response_time += duration_sec
            if status_code >= 400:
                self._error_count += 1

    def record_auth_attempt(self) -> None:
        with self._lock:
            self._auth_attempts += 1

    def record_marketplace_tx(self) -> None:
        with self._lock:
            self._marketplace_txs += 1

    def record_retirement_op(self) -> None:
        with self._lock:
            self._retirement_ops += 1

    def record_db_query(self) -> None:
        with self._lock:
            self._db_queries += 1

    def record_cache_hit(self) -> None:
        with self._lock:
            self._cache_hits += 1

    def record_cache_miss(self) -> None:
        with self._lock:
            self._cache_misses += 1

    def get_metrics(self) -> Dict[str, Any]:
        with self._lock:
            avg_resp = (self._total_response_time / self._total_requests * 1000) if self._total_requests > 0 else 0.0
            err_rate = (self._error_count / self._total_requests) if self._total_requests > 0 else 0.0
            
            total_cache_reqs = self._cache_hits + self._cache_misses
            hit_ratio = (self._cache_hits / total_cache_reqs) if total_cache_reqs > 0 else 0.0
            miss_ratio = (self._cache_misses / total_cache_reqs) if total_cache_reqs > 0 else 0.0
            
            return {
                "total_requests": self._total_requests,
                "average_response_time_ms": round(avg_resp, 2),
                "error_rate": round(err_rate, 4),
                "authentication_attempts": self._auth_attempts,
                "marketplace_transactions": self._marketplace_txs,
                "retirement_operations": self._retirement_ops,
                "database_queries": self._db_queries,
                "cache_hit_ratio": round(hit_ratio, 4),
                "cache_miss_ratio": round(miss_ratio, 4)
            }


metrics_service = MetricsService()
