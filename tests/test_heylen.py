import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from backend.sources.heylen import parse_embedded_listings, is_analyzable, parse_heylen_detail
from backend.sources.antwerp import is_antwerp_postcode

SAMPLE = r'''\"ID\":332301,\"Goal\":0,\"Street\":\"Roest\",\"HouseNumber\":\"8\",\"BoxNr\":\"62\",\"Zip\":\"2600\",\"City\":\"Berchem\",\"Price\":\"209000\",\"NumberOfBedRooms\":1,\"NumberOfBathRooms\":1,\"SurfaceTotal\":41,\"SurfaceGround2\":82,\"Status\":1,\"SubStatus\":2,\"WebID\":\"2\",\"EPCLabelText\":\"C\",\"CreatedDate\":\"2026-08-09 18:01:36\",\"ProjectID\":null,\"SiteID\":16,\"LastChangedDate\":\"2026-08-30 12:33:07\",\"GoogleX\":\"51.18\",\"GoogleY\":\"4.43\",\"x\":1,\"ConstructionYear\":1970'''

def test_parse():
    items = parse_embedded_listings(SAMPLE)
    assert len(items) >= 1
    assert items[0]["price"] == 209000
    assert items[0]["living_area"] == 41
    assert items[0]["epc_label"] == "C"
    assert is_analyzable(items[0])

def test_pc():
    assert is_antwerp_postcode("2600")

if __name__ == "__main__":
    test_parse(); test_pc(); print("PASS")
