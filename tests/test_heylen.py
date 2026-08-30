import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from backend.sources.heylen import parse_heylen_detail, data_quality, is_analyzable, _extract_listing_urls
from backend.sources.antwerp import is_antwerp_postcode

SAMPLE = '''<script type="application/ld+json">
{"@context":"https://schema.org","@type":"RealEstateListing",
 "name":"Huis in Hoboken","description":"Woning 120 m2 te renoveren",
 "image":"https://example.com/a.jpg",
 "offers":{"@type":"Offer","price":565000,"priceCurrency":"EUR"},
 "address":{"@type":"PostalAddress","streetAddress":"Straat 1","addressLocality":"Hoboken","postalCode":"2660","addressCountry":"BE"}}
</script>'''

def test_parse_heylen_jsonld():
    item = parse_heylen_detail(SAMPLE, "https://www.heylenvastgoed.be/kopen/huis-te-koop-in-hoboken/334538")
    assert item["price"] == 565000
    assert item["postal_code"] == "2660"
    assert item["living_area"] == 120
    assert is_analyzable(item)

def test_extract_urls():
    urls = _extract_listing_urls('<a href="/kopen/huis-te-koop-in-hoboken/334538">x</a>')
    assert any("334538" in u for u in urls)

def test_antwerp_pc():
    assert is_antwerp_postcode("2660")
    assert not is_antwerp_postcode("2300")

if __name__ == "__main__":
    test_parse_heylen_jsonld(); test_extract_urls(); test_antwerp_pc()
    print("ALL PASS")
