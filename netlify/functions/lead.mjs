// Lead form proxy — server-side validation + api_key injection
// Forms send a 'page_id' (not api_key); function maps page_id → api_key from PRIVATE_KEYS
// Bots scraping the public HTML cannot get the LeadSnap api_key.
// Keys are inlined below (server-side function code, never served as a public file).

const KEYMAP = {
  "home": "QeqPmDWwFvlrHV9INQ5nSPZIBh1YdJTh",
  "about-us": "QeqPmDWwFvlrHV9INQ5nSPZIBh1YdJTh",
  "privacy-policy": "QeqPmDWwFvlrHV9INQ5nSPZIBh1YdJTh",
  "locations": "QeqPmDWwFvlrHV9INQ5nSPZIBh1YdJTh",
  "locations/foundation-repair-chattanooga-tn": "F4FifUlIi56YsrH3whsMcPihRwlcuDiN",
  "locations/foundation-repair-milwaukee-wi": "IEXytY5qMjiYt0IA5r3JCza4jefZE1LY",
  "locations/foundation-repair-greenville-sc": "47Jl7wkD26E9PuiMHZxpOu1SAGaHYaBX",
  "locations/foundation-repair-pittsburgh-pa": "eAQSjdxObaet7OFlSB9CazTH7D1HktcY",
  "locations/foundation-repair-worcester-ma": "jWhqJFIf4ZfeTrAxtIK8wtNYCPBVMJMr",
  "locations/foundation-repair-port-charlotte-fl": "QvMPDKm2A8H4uvtJbFFlV0IKICTZ3soJ",
  "locations/foundation-repair-concord-nc": "RN2uOHnzha2fDjNje7dOlqMZw63ikeHm",
  "locations/foundation-repair-baltimore-md": "X1S9hx24VQT4dz8UdFxd8RhZk4jFbd8t",
  "locations/foundation-repair-tallahassee-fl": "PLMucg22SY833n6Gfg2FC5pfHu6Q6Ld7",
  "locations/foundation-repair-jacksonville-nc": "BNMOUGMckRQ74wou1sLJ7rxz4pR2v54Q",
  "locations/foundation-repair-columbia-sc": "ZNVH6wNajW01oI4CFSqu1nEGhHpgsW0Z",
  "locations/foundation-repair-reidsville-nc": "wXtLTJynognNu24jytpGU34QbsImrmKr",
  "locations/foundation-repair-dayton-oh": "15U3Ny9y99O5TnX5GelinDiFmRvIAzEF",
  "locations/foundation-repair-tulsa-ok": "Mg2H8mWa9UDaHxXh020xihtJVl6BoLYn",
  "locations/foundation-repair-albany-ny": "lGkDY7v4gTwCwDUHISIxO65fiF6fQakk",
  "locations/foundation-repair-johnson-city-tn": "5GJeENsCuILr3dnI5dBkMdGlXdLsNOHZ",
  "locations/foundation-repair-matthews-nc": "JsckdKtj4nfNSfVFTpCknGlpEIe1VZ0r",
  "locations/foundation-repair-syracuse-ny": "MQrFbn5bxcZlL1cczzYKRXlK0LlrWYv7",
  "locations/foundation-repair-asheville-nc": "pX2qKuXbvu59GPo1JNp3AJWX4VZZUz5J",
  "locations/foundation-repair-fort-worth-tx": "Ngl7uhpQnI2GKfF8C6Ue0nThohocT0zD",
  "locations/foundation-repair-durham-nc": "Zr6l7VVdeErl8NQEhGuxyuO5dpJ8pEE1",
  "locations/foundation-repair-rock-hill-sc": "Vn4KOHKRXWbqnfNXy9P5TxP6z6Jh2byS",
  "locations/foundation-repair-cleveland-oh": "QriIca7znpsJIJ66GZzDDSv3KxSzTjdh",
  "locations/foundation-repair-augusta-ga": "k4nmedaZbkxQugZ5PJ0L4zPjHFHmrhPk",
  "locations/foundation-repair-columbus-oh": "ZlOkBtVFll1ICMkdVplSdooveIutr9MD",
  "locations/foundation-repair-erie-pa": "aTxfPWCOd54APnXRTkQq0STkrCGhOQ4A",
  "locations/foundation-repair-mansfield-tx": "GJ7WOpqCyke8ZF3QxmgAeC2QFcvBzItR",
  "locations/foundation-repair-akron-oh": "YSForyGoVkQhblBalNIEDQEiGMJvu9Dc",
  "locations/foundation-repair-chicago-il": "pxudqTkwFqYCmkIVUU9IyOSineY7YDTe",
  "locations/foundation-repair-minneapolis-mn": "yOzq3K7dS35wKpzLIi8CEM2yMhzLPa3c",
  "locations/foundation-repair-lynchburg-va": "tis8nCN5ylMg6TEhWVxxqDSB0BbmwE4z",
  "locations/foundation-repair-richmond-va": "nhGQBjx8g59yaDJl0sba57fRNBy4EZaC",
  "locations/foundation-repair-alexandria-va": "qdCHnfGYZxSfL5QVRx0kiawhUaYkQjmn",
  "locations/foundation-repair-cincinnati-oh": "906QdVVxmJaVFe5Nht2442o87DviotFj",
  "locations/foundation-repair-roanoke-va": "JWHV9QJ4cr2rlEyleqghtSfRi0kZT2Vt",
  "locations/foundation-repair-birmingham-al": "kZuXxxqZmAL6jpzhcL0KV3EmqNifs4Nw",
  "locations/foundation-repair-chesapeake-va": "HHeO7NY92vhxEvjwfsrKMrUSVAj4iqGa",
  "locations/foundation-repair-boston-ma": "sHBCpqYtIeXVPvf6wzdNUDlHqA67yoaK",
  "locations/foundation-repair-philadelphia-pa": "VNnDkHeaENECr5YAAyZb1yB8m6F4jKyd",
  "locations/foundation-repair-greensboro-nc": "xMdyDaoxQvW0BfPA4P7LhC5PYGqDC3Mu",
  "locations/foundation-repair-atlanta-ga": "0XhqAEGoYlOOeME7hzRMicn7DqSeMJWW",
  "locations/foundation-repair-sarasota-fl": "cSjjUh1feVn8ZPWLdj3SGwkPYD9SHUBU",
  "locations/foundation-repair-jacksonville-fl": "bQJ2WYxXbFf4jgWEaZtu21UAOr7UtmV3",
  "locations/foundation-repair-youngstown-oh": "yTRmPo4H5d5nrsEgbmxIFXtk3jlAg3tv",
  "locations/foundation-repair-hickory-nc": "g8SwSoOeU22RIwUfSgjyaQxWBkWqTcWl",
  "locations/foundation-repair-fort-myers-fl": "O9lRdQPIpXUXwaHzS5EQIlYtq4qGiCTL",
  "locations/foundation-repair-charlotte-nc": "vMLojiOZc7sRTvIYAuKuC3IyNp4ZXp2Y",
  "locations/foundation-repair-wilmington-nc": "UOnXGIdmq4qx4Wvo5I1cr2AVfH6sU4N5",
  "locations/foundation-repair-huntsville-al": "62K7tfK77X7IADDmqob54MDg0d4o1tTn",
  "contact-us": "QeqPmDWwFvlrHV9INQ5nSPZIBh1YdJTh",
  "services/foundation-crack-repair": "9ZaDvGJp3oK4pREEMeRxq18A6SojXVzI",
  "services/french-drain-installation": "9ZaDvGJp3oK4pREEMeRxq18A6SojXVzI",
  "services/sump-pump-installation": "9ZaDvGJp3oK4pREEMeRxq18A6SojXVzI",
  "services/helical-pier-installation": "9ZaDvGJp3oK4pREEMeRxq18A6SojXVzI",
  "services/crawl-space-encapsulation": "9ZaDvGJp3oK4pREEMeRxq18A6SojXVzI",
  "services/egress-window-installation": "9ZaDvGJp3oK4pREEMeRxq18A6SojXVzI",
  "services/basement-wall-repair": "9ZaDvGJp3oK4pREEMeRxq18A6SojXVzI",
  "services/basement-waterproofing": "9ZaDvGJp3oK4pREEMeRxq18A6SojXVzI",
  "services/foundation-repair": "9ZaDvGJp3oK4pREEMeRxq18A6SojXVzI",
  "services/crawl-space-repair": "9ZaDvGJp3oK4pREEMeRxq18A6SojXVzI",
  "services/concrete-leveling": "9ZaDvGJp3oK4pREEMeRxq18A6SojXVzI"
};

const LEADSNAP_URL = 'https://app.leadsnap.com/embed/store';
const CYRILLIC_RE = /[Ѐ-ӿԀ-ԯ]/;

export default async (req) => {
  if (req.method !== 'POST') {
    return new Response('Method Not Allowed', { status: 405 });
  }

  let body;
  try { body = await req.text(); }
  catch { return jsonOk(); }

  const params = new URLSearchParams(body);

  // 1. Honeypot check
  if (params.get('website')) return jsonOk();

  // 2. Cyrillic check on all text values
  for (const [, value] of params) {
    if (typeof value === 'string' && CYRILLIC_RE.test(value)) return jsonOk();
  }

  // 3. Required fields
  const name = params.get('cf-field[pdf-name]');
  const phone = params.get('cf-field[pdf-phone]');
  if (!name || !phone) return jsonOk();

  // 4. Phone digit check
  const digitCount = (phone.match(/\d/g) || []).length;
  if (digitCount < 7) return jsonOk();

  // 5. Page identifier check — look up api_key server-side
  const pageId = params.get('page_id');
  if (!pageId) return jsonOk();
  const apiKey = KEYMAP[pageId];
  if (!apiKey) return jsonOk(); // unknown page = bot guessing

  // 6. Inject api_key server-side and forward to LeadSnap
  params.set('api_key', apiKey);
  // Remove the page_id before forwarding (LeadSnap doesn't need it)
  params.delete('page_id');

  try {
    await fetch(LEADSNAP_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: params.toString(),
    });
  } catch {}

  return jsonOk();
};

function jsonOk() {
  return new Response(JSON.stringify({ success: true }), {
    status: 200,
    headers: { 'Content-Type': 'application/json' },
  });
}
