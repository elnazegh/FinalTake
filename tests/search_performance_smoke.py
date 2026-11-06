import math
import statistics
import time

from app import app

app.config["TESTING"] = True

scenarios = {
    "Normal search": {"query": "dark"},
    "Filtered search": {
        "query": "dark",
        "genre": "Action",
        "media_type": "movie"
    },
    "Sorted search": {
        "query": "dark",
        "sort": "year_desc"
    },
    "No matching results": {
        "query": "zzzz_nonexistent_item"
    }
}

client = app.test_client()
iterations = 50

print("FC4G6-827 — Search API Performance Smoke Test")
print(f"Requests per scenario: {iterations}")
print()

for name, parameters in scenarios.items():
    for _ in range(5):
        client.get("/api/search", query_string=parameters)

    timings = []

    for _ in range(iterations):
        start = time.perf_counter()
        response = client.get(
            "/api/search",
            query_string=parameters
        )
        elapsed = (time.perf_counter() - start) * 1000

        assert response.status_code == 200, name
        assert isinstance(response.get_json()["results"], list), name

        timings.append(elapsed)

    sorted_timings = sorted(timings)
    p95_index = math.ceil(0.95 * iterations) - 1

    print(name)
    print(f"  Median: {statistics.median(timings):.3f} ms")
    print(f"  P95:    {sorted_timings[p95_index]:.3f} ms")
    print(f"  Max:    {max(timings):.3f} ms")
    print()
