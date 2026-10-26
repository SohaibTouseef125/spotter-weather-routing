# Spotter Assessment — Weather-Aware Truck Routing
**Role:** Full Stack Developer (Spotter) · **Stack:** React + Django
**Waqt:** 4 din, 16 working hours se zyada NAHI · **Deadline:** ~Oct 27 shaam PKT (brief 23 Oct shaam ko mila)
**Bonus:** $100 agar assessment kamyab raha
**Deliverables:** GitHub repo + hosted live app + Loom walkthrough video

---

## App kya karegi (1 line concept)
Truck ke route par har thori door ke baad **mausam check** karke driver ko pehle se **alert** de — masalan "mile 120 par tez barish" — taake woh route badal le ya ruk jaye.

## Architecture (simple)
```
[React UI — Leaflet map]  ⇄  [Django API]  ⇄  free services:
   | origin/destination input      | /api/route/        | OSRM (route line)
   | map par route + weather       | /api/weather/      | Open-Meteo (mausam)
   | alerts ki list                | merge karke bhejta | dono ka jawab jor kar
```
- **Django** sirf API deta hai (koi HTML page nahi) — isay kehte hain "backend sirf data serve karta hai".
- **React** sirf screen dikhata hai — user input leta hai, API se data la kar map par dikhata hai.
- Dono ke beech **JSON** bolta hai.

## Free APIs (koi key nahi chahiye, koi paisa nahi)
1. **OSRM routing** — do points do, poora route (lat/lng points) milta hai:
   `https://router.project-osrm.org/route/v1/driving/{lng1},{lat1};{lng2},{lat2}?overview=full&geometries=geojson`
2. **Open-Meteo weather** — key bilkul nahi chahiye:
   `https://api.open-meteo.com/v1/forecast?latitude=..&longitude=..&hourly=temperature_2m,precipitation_probability,weathercode,windspeed_10m`
   `weathercode` ka matlab: 0=saaf, 1–3=badal, 45/48=kohra, 51–67=barish, 71–77=barf, 80–82=tez barish, 95–99=toofan.
3. **Nominatim geocoding** — sheher ka naam → lat/lng (sirf Django se call karna, browser se nahi):
   `https://nominatim.openstreetmap.org/search?q=Lahore&format=json&limit=1` (header mein User-Agent dena zaroori)

## 16 ghante ka budget (sakhti se)
| Din | Ghante | Kaam |
|---|---|---|
| 1 | 4 | Django project + `/api/route/` endpoint (OSRM call), curl se test |
| 2 | 5 | `/api/weather/` endpoint (route ke har ~50 km point par Open-Meteo), dono ka merge → ek JSON (route + weather points + alerts) |
| 3 | 5 | React UI: origin/destination form, Leaflet map par route line, weather badges, alerts list |
| 4 | 2 | Deploy (neeche), choti fixes, Loom record, submission bhej do |

**Scope kaat do (jeet ka raaz):** login/signup MAT banao, database MAT banao (in-memory hi kaafi), truck fleet management MAT banao. Sirf: do sheher → route → mausam → alerts. Bas.

## Alerts ka simple rule (tumhara logic — yahin marks hain)
Route ke har waypoint par weather code dekho:
- `weathercode >= 95` → 🔴 "Toofan — route rokne ka mashwara"
- `80–82` ya `precipitation_probability > 70` → 🟡 "Tez barish — speed kam"
- `45/48` → 🟡 "Kohra — headlights/low speed"
- `windspeed_10m > 60` → 🟡 "Tez hawa"
- warna 🟢 "Saaf"

## Deploy (dono free)
- **Backend:** render.com → New Web Service → GitHub repo ka `backend/` → Build: `pip install -r requirements.txt` → Start: `gunicorn weather_route.wsgi` (requirements mein gunicorn add karna). Free tier sota hai (pehli request slow) — Loom se pehle ek dafa khol lena.
- **Frontend:** vercel.com → repo ka `frontend/` import → env variable `VITE_API_URL=<render ka URL>` → Deploy.
- **Loom:** ≤3 min — form bharo → route dikhao → ek alert point par click → "yeh maine banaya" → khatam.

## Checklist (submit se pehle)
- [ ] Repo public, README mein run instructions
- [ ] Live backend URL kaam karta hai (curl test)
- [ ] Live frontend backend se baat karta hai (CORS on — settings mein hai)
- [ ] Loom video ≤3 min, link public
- [ ] Ena ko email (neeche template)

## Ena ko submission email (template)
> Hi Ena,
>
> I've completed the assessment — Weather-Aware Truck Routing app.
>
> GitHub: <repo link>
> Live app: <frontend link>
> Walkthrough (3 min): <Loom link>
>
> Built with React + Django: enter origin and destination, the app draws the truck route on a map, checks live weather at intervals along the route (Open-Meteo), and raises alerts for storms, heavy rain, fog and high wind so the driver can plan ahead.
>
> Happy to walk through the code on a call.
>
> Best regards,
> Sohaib Touseef

## `scaffold/` folder kya hai
Khali project ka dhancha — `django-admin startproject` jaisa, taake setup mein 1 ghanta bache. **Logic tum likho ge** (views mein TODO likhe hain). `README.md` har folder mein hai.
