# Student Dashboard Integration Instructions

This file documents the exact steps required to integrate the new isolated Student Dashboard into the Sevafy React application. Please follow these steps on your workstation.

## Step 1: Transfer Files
Move the two created files from this folder (`student_page_folder`) into your main React project's `pages` folder.

```bash
mv student_page_folder/StudentDashboard.jsx src/pages/
mv student_page_folder/StudentDashboard.module.css src/pages/
```

## Step 2: Show ONLY the "I'm a Student" Card
To ensure the landing page strictly targets students and removes the other portal cards (as requested), you must update the `PORTALS` constant.

Open `src/constants.js` and **replace** the `PORTALS` array (around line 18) with the following filtered version:

```javascript
export const PORTALS = [
  {
    id: 'student',
    label: 'Student',
    heading: "I'm a Student",
    description:
      'Access ML-verified authentic scholarships. No fake leads, no wasted applications.',
    url: '/login', // Modified to route locally
  }
];
```

## Step 3: Register the Student Page Route
Open `src/App.jsx`. You need to ensure students are directed to this page when they click "Dashboard".

1. **Import the new component** at the top of `App.jsx`:
```javascript
import StudentDashboard from './pages/StudentDashboard';
```

2. **Add a new Route** inside the `<Routes>` block (around line 105):
```javascript
<Route path="/student-dashboard" element={<StudentDashboard />} />
```

## Step 4: Ensure Students Access Their Dashboard
You need to ensure that when a user with the `STUDENT` role logs in, they are directed to the new `StudentDashboard`. You can manage this by modifying `src/components/PortalSection.jsx` and `src/App.jsx` as follows:

In `src/components/PortalSection.jsx`, locate the `ROLE_TO_DASHBOARD` object (around line 44) and update the path for the student:

```javascript
const ROLE_TO_DASHBOARD = {
  DONATOR: { label: 'Donor', path: '/dashboard', iconKey: 'donor' },
  STUDENT: { label: 'Student', path: '/student-dashboard', iconKey: 'student' },
  NGO_PERSONNEL: { label: 'Partner (NGO)', path: '/dashboard', iconKey: 'ngo' },
};
```

In `src/App.jsx`, update the NavBar "Dashboard" link logic (around line 46) to route based on the current user's role:
```javascript
<Link to={user.role === 'STUDENT' ? '/student-dashboard' : '/dashboard'} className="btn btn-ghost">
  Dashboard
</Link>
```

By completing these steps, the isolated, highly mobile-responsive `StudentDashboard` will be fully integrated.
