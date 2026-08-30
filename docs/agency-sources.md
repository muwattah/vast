# Antwerp agency websites survey

| Agency | Status | Antwerp yield |
|--------|--------|---------------|
| **Heylen** | ACTIVE connector | 561 with price/m2 |
| **Walls** | ACTIVE connector | 123 with price+PC |
| Arcasa | Public HTML | ~88 regional |
| Las Immo / Immo C&S | Public HTML | Small |
| Omnia / Dewaele | Public but complex | Not yet parsed |
| Immoweb/Zimmo/Immovlan | NOT_SUPPORTED | Cloudflare |

```bash
curl -X POST "http://localhost:8000/api/sources/heylen/run?limit=600"
curl -X POST "http://localhost:8000/api/sources/walls/run?limit=150"
```
