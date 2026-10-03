# GeoAttend – Location-Based Attendance System
## Technical Documentation

**Version:** 1.0.0
**Date:** October 2026
**Author:** GeoAttend Team
**Status:** Awaiting Approval

---

## Table of Contents
1. [Project Overview](#1-project-overview)
2. [System Architecture](#2-system-architecture)
3. [Technology Stack](#3-technology-stack)
4. [File Structure](#4-file-structure)
5. [Core Features](#5-core-features)
6. [Geofencing Logic](#6-geofencing-logic)
7. [Data Models](#7-data-models)
8. [API and Storage Layer](#8-api-and-storage-layer)
9. [UI Components](#9-ui-components)
10. [Security Considerations](#10-security-considerations)
11. [Performance Notes](#11-performance-notes)
12. [Known Limitations](#12-known-limitations)
13. [Future Roadmap](#13-future-roadmap)
14. [Setup and Deployment](#14-setup-and-deployment)

---

## 1. Project Overview

**GeoAttend** is a browser-based, GPS-powered attendance management system that uses HTML5 Geolocation API and geofencing to verify employee presence at registered locations before recording attendance.

### Goals
- Allow employees to mark attendance only when physically present within a registered location zone
- Provide managers with real-time visibility into attendance status
- Generate analytics reports on attendance trends, late arrivals, and zone utilization
- Work fully client-side with no backend dependency (MVP phase)

### Target Users
| Role | Description |
|------|-------------|
| **Employee** | Marks check-in and check-out; views own records |
| **Manager** | Views team records, reports, zone management |
| **Administrator** | Full access: settings, data export, zone configuration |

---

## 2. System Architecture

```
Browser (Client)
|
|-- index.html  (Structure)
|-- styles.css  (Design)
|-- app.js      (Application Logic)
       |
       |-- GPS Module      (navigator.geolocation)
       |-- Charts Module   (Chart.js CDN)
       |-- Storage Module  (localStorage)
```

### Data Flow

```
User Opens App
    --> Load from LocalStorage (records, zones, settings, session)
    --> Start GPS Watch (watchPosition)
         |-- Coords Available --> Check Against Zones --> Show Zone Match
         |-- Location Error  --> Show Error Message
    --> User Clicks Check In
         --> Validate Form Fields
         --> Validate GPS Fix
         --> Determine Status (present / late) via settings
         --> Create Record Object
         --> Save to LocalStorage
         --> Update UI (session timer, activity feed, stats)
```

---

## 3. Technology Stack

| Layer | Technology | Version | Notes |
|-------|-----------|---------|-------|
| **Markup** | HTML5 | — | Semantic elements, accessible |
| **Styling** | Vanilla CSS3 | — | Custom properties, Grid, Flexbox |
| **Logic** | Vanilla JavaScript | ES2020+ | strict mode, no framework |
| **Charts** | Chart.js (CDN) | 4.4.2 | Bar, Line, Doughnut charts |
| **Fonts** | Google Fonts (Inter) | — | CDN loaded |
| **Storage** | Browser LocalStorage | — | ~5MB limit per origin |
| **Location** | HTML5 Geolocation API | — | Browser-native |

> No build tools, no npm, no framework. The entire app runs from 3 files: `index.html`, `styles.css`, `app.js`.

---

## 4. File Structure

```
webapp/
|
|-- index.html          # App shell, page sections, modals
|-- styles.css          # Full design system and component styles
|-- app.js              # All application logic
|-- TECHNICAL_DOCS.md   # This document
```

### File Responsibilities

| File | Lines | Responsibility |
|------|-------|----------------|
| `index.html` | ~250 | DOM structure, all pages, modals, nav |
| `styles.css` | ~680 | Design tokens, components, responsive, animations |
| `app.js` | ~580 | State management, GPS, geofence, charts, persistence |

---

## 5. Core Features

### 5.1 Dashboard
- Live stat cards: Present, Absent, Late, Active Zones
- Quick Check-In / Check-Out button with GPS status
- Today's activity feed (real-time)
- Monthly attendance bar chart (last 30 days)

### 5.2 Check-In / Check-Out
- Live GPS coordinate display with accuracy
- Animated GPS pulse indicator
- Zone proximity auto-detection
- Full attendance form (Name, ID, Department, Zone, Notes)
- Active session timer (persists on refresh)

### 5.3 Attendance Records
- Full tabular history of all records
- Filters by date and employee name/ID
- Paginated (10 records per page)
- Record detail modal (view full info)
- Delete individual records
- CSV export

### 5.4 Location Zones
- Create, edit, delete geofence zones
- Zone types: Office, Field, Remote, Client
- Visual map representation with zone circles
- User location pin on the map

### 5.5 Reports and Analytics
- Time period selector (7 / 30 / 90 days)
- KPI cards: Avg Rate, Avg Hours, Top Dept, Late Count
- Line chart: Attendance Trend
- Doughnut chart: Department Breakdown
- Bar chart: Zone Utilization

### 5.6 Settings
- Work hours configuration (start/end time)
- Late threshold (minutes)
- Default geofence radius
- Profile (Name, Role, Email)
- Data management (export, demo data, clear all)

### 5.7 UX Features
- Dark / Light theme toggle (persisted)
- Live clock in navbar
- Toast notification system (Success, Error, Warning, Info)
- Session persistence (active check-in survives page refresh)
- Responsive design (mobile-friendly)

---

## 6. Geofencing Logic

### Haversine Formula
Distance calculation between two GPS coordinates uses the Haversine formula:

```javascript
const distance = (lat1, lon1, lat2, lon2) => {
  const R = 6371000; // Earth radius in metres
  const phi1 = lat1 * Math.PI / 180;
  const phi2 = lat2 * Math.PI / 180;
  const dPhi = (lat2 - lat1) * Math.PI / 180;
  const dLam = (lon2 - lon1) * Math.PI / 180;
  const a = Math.sin(dPhi/2)**2 + Math.cos(phi1)*Math.cos(phi2)*Math.sin(dLam/2)**2;
  return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
};
```

### Zone Match Logic
```javascript
const matched = state.zones.find(zone =>
  distance(userLat, userLng, zone.lat, zone.lng) <= zone.radius
);
```

If the calculated distance is within the zone's configured radius, the user is **inside** the zone and check-in is permitted.

### Late Detection
```javascript
const getAttendanceStatus = (checkInTime) => {
  const [sh, sm] = state.settings.startTime.split(':').map(Number);
  const threshold = sh * 60 + sm + state.settings.lateThreshold;
  const actual = checkInTime.getHours() * 60 + checkInTime.getMinutes();
  return actual <= threshold ? 'present' : 'late';
};
```

| Check-in Time | Start Time | Threshold | Status |
|---|---|---|---|
| 08:50 | 09:00 | +15 min | Present |
| 09:14 | 09:00 | +15 min | Present |
| 09:20 | 09:00 | +15 min | Late |
| 11:00 | 09:00 | +15 min | Late |

---

## 7. Data Models

### 7.1 Attendance Record
```javascript
{
  id:        "1696327200_abc123",
  name:      "Rahul Sharma",
  empId:     "EMP-001",
  dept:      "Engineering",
  zoneName:  "Main Office",
  zoneId:    "1696300000_xyz789",
  notes:     "Working late today",
  checkIn:   "2026-10-03T09:05:00.000Z",
  checkOut:  "2026-10-03T18:02:00.000Z",  // null if active
  duration:  "8h 57m",                    // null if active
  lat:       18.52045,
  lng:       73.85671,
  accuracy:  12.5,                        // meters
  status:    "present"                    // "present" | "late" | "absent"
}
```

### 7.2 Location Zone
```javascript
{
  id:         "1696300000_xyz789",
  name:       "Main Office",
  address:    "Tech Park, Pune",
  lat:        18.5204,
  lng:        73.8567,
  radius:     150,
  type:       "office",   // "office" | "field" | "remote" | "client"
  createdAt:  "2026-10-01T10:00:00.000Z"
}
```

### 7.3 Settings
```javascript
{
  startTime:      "09:00",
  endTime:        "18:00",
  lateThreshold:  15,
  radius:         100,
  name:           "Admin User",
  role:           "Administrator",
  email:          "admin@company.com",
  theme:          "dark"   // "dark" | "light"
}
```

### 7.4 Active Session
```javascript
{
  recordId:   "1696327200_abc123",
  startTime:  "2026-10-03T09:05:00.000Z"
}
```

---

## 8. API and Storage Layer

### LocalStorage Keys
| Key | Content | Size (typical) |
|-----|---------|---------------|
| `geoattend_v2_records` | Array of records (JSON) | 1-50 KB |
| `geoattend_v2_zones` | Array of zones (JSON) | < 5 KB |
| `geoattend_v2_settings` | Settings object (JSON) | < 1 KB |
| `geoattend_v2_session` | Active session (JSON) | < 1 KB |

### Persistence Functions
```javascript
save() // Serializes all state to localStorage
load() // Deserializes from localStorage into state object
```

### GPS Watching
```javascript
navigator.geolocation.watchPosition(
  successCallback,
  errorCallback,
  { enableHighAccuracy: true, timeout: 15000, maximumAge: 5000 }
)
```

The watcher fires every time the device position changes significantly and updates all location-dependent UI elements.

---

## 9. UI Components

### Component Inventory

| Component | Location | Description |
|-----------|----------|-------------|
| Navbar | index.html | Fixed top bar with branding, clock, theme toggle |
| Sidebar | index.html | Fixed left nav with page links and user card |
| Stat Cards | Dashboard | KPI metrics with colored accent borders |
| GPS Display | Check-in page | Animated pulse rings + coordinate display |
| Zone Map | Check-in page | CSS-rendered proportional map with zone circles |
| Activity Feed | Dashboard | Scrollable real-time activity log |
| Data Table | Records page | Records with filters and pagination |
| Zone Cards | Locations page | Zone cards with edit/delete actions |
| Charts | Dashboard + Reports | Chart.js integrated canvases |
| Modals | Global | Zone form, Record detail |
| Toasts | Global | Stacked notifications with auto-dismiss |

### Design System Color Tokens
```
--accent:       #6366f1   (Indigo primary)
--success:      #22c55e   (Green)
--danger:       #ef4444   (Red)
--warning:      #f59e0b   (Amber)
--info:         #3b82f6   (Blue)
--bg-primary:   #0d0f17   (Deep dark background)
--bg-card:      #1a1d2e   (Card background)
--text-primary: #f0f2ff   (Primary text)
--radius:       12px      (Default border radius)
```

---

## 10. Security Considerations

| Risk | Mitigation |
|------|-----------|
| GPS spoofing | Accuracy displayed to admin; high-accuracy mode enforced |
| Data tampering | LocalStorage is client-side; backend integration required for production |
| XSS | Display uses escaped template literals; no raw innerHTML with user input |
| Session hijacking | No server auth in MVP; OAuth integration planned for Phase 2 |
| Data privacy | All data stored locally; nothing sent to external servers |

> **For production**: Replace LocalStorage with an authenticated REST API or Firebase backend. Add server-side GPS verification using IP geolocation as secondary confirmation.

---

## 11. Performance Notes

- **GPS watch**: Uses `watchPosition` with `maximumAge: 5000` to cache results for 5s, reducing battery drain
- **Charts**: `destroyChart()` called before re-rendering to prevent Chart.js memory leaks
- **DOM Updates**: Records table uses `innerHTML` batch update for efficiency on filter changes
- **LocalStorage**: Writes on every user action; debounce saves for datasets >1000 records
- **Pagination**: Records sliced client-side (10/page); table render is fast regardless of total count

---

## 12. Known Limitations

| Item | Description |
|------|-------------|
| **No backend** | Data is browser-local; lost if localStorage is cleared |
| **Single user** | No multi-user auth; all users share the same browser data |
| **GPS on mobile** | iOS Safari requires HTTPS for geolocation |
| **GPS accuracy** | Indoor GPS can be inaccurate (+/-50-100m); beacon/QR fallback needed |
| **No real map** | Zone map is CSS visualization, not a real tile map |
| **No push notifications** | Check-in/out reminders not implemented |
| **CSV only** | No PDF or Excel export |

---

## 13. Future Roadmap

### Phase 2 - Backend Integration
- [ ] Firebase Firestore for multi-user data storage
- [ ] Firebase Authentication (Google / Email login)
- [ ] Server-side attendance validation
- [ ] Real-time dashboard with WebSockets

### Phase 3 - Enhanced Features
- [ ] Google Maps API integration for real zone map
- [ ] QR Code / NFC fallback for indoor check-in
- [ ] Beacon-based proximity (Bluetooth LE)
- [ ] Push notifications for check-in reminders
- [ ] Facial recognition via WebRTC as secondary verification
- [ ] PDF report generation
- [ ] Slack / Teams integration

### Phase 4 - Enterprise Features
- [ ] LDAP / Active Directory integration
- [ ] Shift management and scheduling
- [ ] Leave management integration
- [ ] Payroll system export (ADP, SAP)
- [ ] Role-based access control (RBAC)
- [ ] Audit trail and compliance reporting
- [ ] Mobile apps (React Native / Flutter)

---

## 14. Setup and Deployment

### Local Development
No build step required. Open index.html directly or use a local server:

```bash
# Option 1: Direct open (no GPS on mobile)
open /Users/vishalbulbule/Documents/GCAI-Sep/webapp/index.html

# Option 2: Python HTTP server (recommended for GPS testing)
cd /Users/vishalbulbule/Documents/GCAI-Sep/webapp
python3 -m http.server 8080
# Then open: http://localhost:8080
```

> GPS on Mobile: The Geolocation API requires HTTPS on mobile devices. Use ngrok or deploy to a hosting provider for mobile testing.

### Static Hosting Options

| Platform | Steps |
|----------|-------|
| **GitHub Pages** | Push to `gh-pages` branch or `/docs` folder |
| **Netlify** | Drag-and-drop the `webapp/` folder at netlify.com |
| **Vercel** | Run `vercel deploy` in the project directory |
| **Firebase Hosting** | `firebase init hosting` then `firebase deploy` |
| **Google Cloud Storage** | `gsutil rsync -r webapp/ gs://your-bucket` |

### Browser Compatibility

| Browser | GPS | Charts | Storage | Status |
|---------|-----|--------|---------|--------|
| Chrome 90+ | Yes | Yes | Yes | Fully Supported |
| Firefox 88+ | Yes | Yes | Yes | Fully Supported |
| Safari 14+ | Yes* | Yes | Yes | Supported (HTTPS only for GPS) |
| Edge 90+ | Yes | Yes | Yes | Fully Supported |
| Mobile Chrome | Yes | Yes | Yes | Fully Supported |
| Mobile Safari | Yes* | Yes | Yes | Supported (HTTPS required) |

*Safari requires explicit user permission for geolocation on each session.

---

## Appendix: Quick Start Guide

1. **Open the App** - Load demo data from Settings > Load Demo Data
2. **Add a Zone** - Go to Locations > Add Zone, fill in name and coordinates
3. **Mark Attendance** - Go to Check In/Out, fill in your details, click Check In
4. **View Records** - Go to Records to see all attendance history
5. **Export Data** - Click Export CSV in Records page
6. **View Analytics** - Go to Reports for charts and KPIs

---

*Document generated: October 2026 | GeoAttend v1.0.0*
