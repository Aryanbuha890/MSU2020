# MSU VISION 2020 — Frontend Implementation Plan

> Every UI/UX item from all 4 planning documents is covered. Nothing is skipped.

---

## Phase 1 — Global Layout & Navigation

### 1.1 Navbar Overhaul — Per-Persona Visibility (Doc 4 §2)
- **File**: `templates/base.html`
- **Current**: Static nav shows all links (Needs, Projects, Events, Rollup, Funding, Pools, Governance, Profile) to everyone; Governance is conditionally shown for gov/admin
- **Required**: Show ONLY pages the user's persona(s) can access (Doc 4 §2 matrix)
- **Implementation**:
  - Replace hardcoded nav links with template variables from the new `persona_nav_items` context processor
  - Each nav item is a dict: `{url, label, active, icon}`
  - Template iterates over `nav_items` list and renders only what's provided
  - Multi-role users see the UNION of all their roles' nav items

**Per-persona nav items (from Doc 4 §2):**

| Persona | Nav Items |
|---------|-----------|
| Foundation Admin | Needs · Projects · Programs · Events · Rollup · Funding · Pools · Governance · Upload Audit Log · Profile |
| HOD / Dean | Needs · Projects · Events · Role Requests · Profile |
| Donor | My Contributions · My Projects · Events · Role Requests · Profile |
| Project Lead | My Projects · Events · Rollup · Role Requests · Profile |
| Volunteer | My Assignments · Events · Role Requests · Profile |
| Finance Controller | Funding · Pools · Projects · Rollup · Governance · Role Requests · Profile |
| Governance Team | Needs · Projects · Programs · Events · Rollup · Governance · Role Requests · Upload Audit Log · Profile |
| Auditor | Needs · Projects · Funding · Rollup · Upload Audit Log · Profile |

### 1.2 Mobile Hamburger Menu (M-01)
- **File**: `templates/base.html`
- **Current**: `flex-wrap` nav breaks on mobile — items stack awkwardly
- **Required**: Hamburger toggle button visible below 768px; nav items collapse into a dropdown panel
- **Implementation**:
  - Add a `<button id="nav-toggle">` with hamburger icon (three horizontal lines)
  - Wrap nav links in a `<div id="nav-menu" class="hidden md:flex">` container
  - Add JS: toggle `hidden` class on click
  - Group secondary items (Pools, Governance, Audit Log) into a "More" dropdown on desktop too
  - CSS: `@media (max-width: 768px)` — full-width vertical nav panel with slide-down animation

### 1.3 Role Switcher Dropdown (Doc 3 §5b)
- **File**: `templates/base.html`
- **Current**: Shows `{{ user.username }}` with logout button
- **Required**: Multi-role users see a dropdown next to username showing their active roles
- **Implementation**:
  - If user has >1 active persona: show a `<select>` or dropdown with all persona labels
  - Selecting a role POSTs to a `switch_role` view → stores active dashboard persona in session
  - Current active role highlighted in dropdown
  - Single-role users see their role label as static text (no dropdown)

### 1.4 CSS Additions
- **File**: `static/css/main.css` (new file, linked from `base.html`)
- Add styles for:
  - Hamburger menu animation
  - Dropdown menus (role switcher, "More" nav group)
  - Progress bars (reusable)
  - Status badges (color-coded by status)
  - Filter/search bar components
  - Modal dialogs
  - Breadcrumb trails
  - Cards with hover effects
  - Alert/notification banners
  - Form validation error styles
  - Mobile-responsive tables (horizontal scroll or card layout on small screens)

---

## Phase 2 — Funding Module Templates

### 2.1 Contribution List — Search, Filter, Sort, Pagination (C-01)
- **File**: `templates/funding/contribution_list.html`
- **Current**: Plain table with all columns, no search/filter/sort/pagination
- **Required**:
  - **Search bar**: Text input above table, filters by donor name, project title, event title
  - **Column filters**: Dropdown filters for Status and Fund Pool (rendered from `ContributionFilter` form)
  - **Sortable headers**: Clickable column headers with up/down arrow icons; link to `?order_by=...`
  - **Pagination**: Bottom controls showing "Page X of Y" with prev/next links; 25 items per page
  - **Filter form layout**: Horizontal bar above table with search input, status select, pool select, sort select, and "Apply" button
  - **Active filters display**: Show active filter tags with "×" to clear each one

### 2.2 Expense List — Same Treatment
- **File**: `templates/funding/expense_list.html`
- **Current**: Plain table
- **Required**: Same search/filter/sort/pagination as contributions
- **Filter fields**: Status, project, fund_pool

### 2.3 Pool List — Balance Cards with Progress Bars (H-02)
- **File**: `templates/funding/pool_list.html`
- **Current**: Simple `<ul>` with pool name, jurisdiction, and description — NO balance data
- **Required**:
  - Replace list with card layout
  - Each card shows:
    - Pool name + jurisdiction badge
    - **Total Collected**: USD amount (green)
    - **Total Allocated**: USD amount (amber)
    - **Remaining**: USD amount (blue)
    - **Utilization progress bar**: width = `(allocated / collected) * 100%`
    - Color: green (<50%), amber (50-80%), red (>80%)
  - Pool description below the stats

### 2.4 Contribution Form — Exchange Rate Display (C-02)
- **File**: `templates/funding/contribution_form.html`
- Show current exchange rate info: "Using rate: 1 USD = 83.33 INR (as of May 2026)"
- Auto-preview USD equivalent as user types amount (JS calculation)

---

## Phase 3 — Dashboard Templates

### 3.1 Dashboard Home — Currency Toggle (C-02)
- **File**: `templates/dashboard/home.html`
- **Current**: Scorecard shows only USD amounts
- **Required**:
  - Add an INR/USD toggle button in the scorecard section header
  - Toggle sends POST to `toggle_currency` view; page reloads with amounts in selected currency
  - Show "Exchange rate: 1 USD = 83.33 INR • Updated: May 17, 2026" below the scorecard
  - Scorecard cards show amounts in selected currency with currency symbol

### 3.2 Project Rollup — Functional Alerts Column (H-01)
- **File**: `templates/dashboard/project_rollup.html`
- **Current**: Alerts column shows "⚠ N overdue" or "—"
- **Required**:
  - Add "🔴 Stalled X days" alert for projects in_progress with 0% milestone progress for 14+ days
  - Add "⚠ N overdue" for overdue milestones (already exists)
  - Add "💰 Tranche awaiting" for milestones with `tranche_governance_status=awaiting_governance`
  - Color coding: red for stalled, amber for overdue, blue for funding pending
  - Tooltip on hover showing detail

### 3.3 Project Rollup — Programs Section (Doc 1 §4b)
- **File**: `templates/dashboard/project_rollup.html`
- **Add** a new section below the projects table: "Programs — Phase Progress"
- **Table columns**: Program name, Phase (current), Progress %, Pool Utilization %, Status, Milestones
- **Each program row** expandable to show child incubator projects underneath
- Visible only to Governance Team and Foundation Admin

### 3.4 Governance Queue — Role Requests Tab (Doc 3 §6)
- **File**: `templates/dashboard/governance_queue.html`
- **Current**: Shows needs, projects, expenses pending governance + persona roster + CSV upload
- **Add section**: "Role Requests" tab/section
  - Table: Username, Requested Role, Reason, Submitted Date, Actions (Approve / Reject)
  - Approve button POSTs to `role_request_approve`
  - Reject button opens inline textarea for reason, then POSTs to `role_request_reject`
  - Badge showing count of pending requests

### 3.5 Governance Queue — CSV Preview Step (Doc 1 §5a)
- **File**: `templates/dashboard/governance_queue.html` (or new partial)
- **Current**: CSV upload directly processes and shows success/error messages
- **Required two-step flow**:
  - Step 1: Upload → show preview summary:
    - "X rows valid, Y rows flagged, Z errors"
    - Table showing flagged rows with reason (duplicate email, invalid persona, etc.)
    - "Confirm Import" and "Cancel" buttons
  - Step 2: On confirm → process rows → show results
  - Use HTMX for inline partial swap (already in stack) or full-page reload

---

## Phase 4 — Profile & Stakeholder Templates

### 4.1 Profile Page Expansion (H-04)
- **File**: `templates/stakeholders/profile_form.html`
- **Current**: Generic form loop with 4 fields (organization, stakeholder_type, jurisdiction, email_opt_in)
- **Required**:
  - **Header section**: User's full name, photo (with upload), persona badge(s), member since date
  - **Personal Info section**: First name, Last name, Batch year, Department, Phone, LinkedIn URL, Bio (textarea)
  - **Account section**: Organization, Jurisdiction, Email opt-in
  - **Role section**: Current role(s) listed as badges; "Request Additional Role" button
  - **Recent Activity section**: Last 10 actions (needs created, milestones updated, contributions made) shown as a timeline list
  - **Pending Role Requests**: If user has pending requests, show status

### 4.2 Role Request Form (Doc 3 §6)
- **File**: NEW `templates/stakeholders/role_request_form.html`
- **Form fields**: Dropdown to select requested persona (exclude already-held), Reason textarea
- **Shown via**: button on Profile page → navigates to this form or opens a modal
- **After submit**: redirect to profile with success message "Request submitted. You'll be notified when reviewed."

### 4.3 Role Request List — User View
- **File**: NEW `templates/stakeholders/role_request_list.html`
- Shows the user's own requests with status badges (Pending=amber, Approved=green, Rejected=red)
- Columns: Role Requested, Reason, Status, Submitted Date, Reviewed By, Review Date

---

## Phase 5 — Event Templates

### 5.1 Event Create/Edit Form (Doc 4 §3)
- **File**: NEW `templates/events/event_form.html`
- **Current**: No create/edit template exists
- **Form fields**: title, description, event_type, venue, location, virtual_link, start_datetime, end_datetime, jurisdiction, status, linked_project, linked_need
- **Fundraising-specific fields** (shown when `event_type=fundraising`):
  - target_amount, fund_pool, target_audience, is_fundraising checkbox
- **Governance workflow notice**: if creating fundraising event, show "This event will start in Draft and require Governance approval before publishing"

### 5.2 Event Detail — Milestones Section (Doc 1 §4a)
- **File**: `templates/events/event_detail.html`
- **Current**: Shows event info, media, registrations
- **Add section**: "Event Milestones" (visible to Governance + Admin + Auditor)
  - Table: Milestone title, Owner, Due date, Status (completed/pending), Proof link
  - "Add Milestone" button (Governance + Admin only)
  - "Mark Complete" button per milestone with proof upload
  - Progress bar showing completed/total milestones

### 5.3 Event Detail — Approval Workflow Status (Doc 1 §4a)
- **File**: `templates/events/event_detail.html`
- Show status badge with workflow: Draft → Governance Approved → Published → Completed
- Transition buttons visible only to authorized personas:
  - "Submit for Governance Approval" (Draft → governance_approved)
  - "Publish" (governance_approved → Published)
  - "Mark Completed" (Published/Ongoing → Completed)

### 5.4 Event Milestone Form
- **File**: NEW `templates/events/event_milestone_form.html`
- **Form fields**: title, owner (dropdown), due_date, notes
- Used for both create and edit

### 5.5 Event List — Status Badges
- **File**: `templates/events/event_list.html`
- Add color-coded status badges
- Add event type badges (fundraising, lecture, networking, recognition)
- Show target amount for fundraising events

---

## Phase 6 — Program Management Templates (NEW) — ✅ COMPLETED

### 6.1 Program List
- **File**: NEW `templates/programs/program_list.html`
- **Table/cards**: Program title, Status badge, Phase (current), Pool, Budget, Progress %
- **"Create Program" button**: visible only to Governance + Foundation Admin
- **Each row**: links to program detail page

### 6.2 Program Detail
- **File**: NEW `templates/programs/program_detail.html`
- **Header**: Title, status badge, originated_by, budget, linked pool
- **Milestones section**: Table grouped by phase
  - Columns: Phase, Milestone Title, Owner, Due Date, Tranche %, Status, Proof
  - "Add Milestone" button (Governance + Admin)
  - "Release Tranche" button per completed milestone with tranche % > 0
- **Linked Projects section**: Table of incubator projects under this program
  - Columns: Project name, Lead, Progress %, Status
- **Pool Utilization section**: Collected vs Allocated vs Remaining for the linked pool

### 6.3 Program Create/Edit Form
- **File**: NEW `templates/programs/program_form.html`
- **Form fields**: title, description, fund_pool, budget, budget_currency, start_date, end_date, owners

### 6.4 Program Milestone Form
- **File**: NEW `templates/programs/program_milestone_form.html`
- **Form fields**: phase (text or select), title, owner, due_date, tranche_percent, notes

---

## Phase 7 — Upload Audit Log Template (NEW) — ✅ COMPLETED

### 7.1 Upload Audit Log List (Doc 4 §5)
- **File**: NEW `templates/core/upload_audit_log.html`
- **Access**: Foundation Admin (full), Governance + Auditor (read-only)
- **Table columns**: Timestamp, Uploader, Filename, File Size, Declared MIME, Actual MIME, Scan Result, Action Taken, Upload Type
- **Filters**: Date range, scan result (clean/flagged/error), upload type, uploader
- **Color coding**: Green rows for clean, Red rows for flagged/quarantined, Amber for errors
- **Pagination**: 50 items per page

---

## Phase 8 — Project Module Template Updates — ✅ COMPLETED

### 8.1 Project Creation UX (H-03)
- **File**: `templates/needs/need_detail.html`
- **Current**: "Add Project" button that redirects to project creation form
- **Required**:
  - Rename button to **"Create Project from Need"**
  - On click: show a **guiding modal** explaining:
    - "You are about to create a funded project linked to this need"
    - "The project budget, description, and funding model will be pre-filled from this need"
    - "You can edit all fields on the next page"
    - Confirm/Cancel buttons
  - After confirmation: redirect to project form
  - **Add breadcrumbs** on project form page: `Needs > [Need Title] > Create Project`

### 8.2 Project Detail — Program Link Display
- **File**: `templates/projects/project_detail.html`
- If project is linked to a program, show "Part of Program: [Program Name]" with link
- Show in the project header section

### 8.3 Project Form — Program Field
- **File**: `templates/projects/project_form.html`
- Add optional "Link to Program" dropdown (for incubator projects)

---

## Phase 9 — Account & Auth Templates — ✅ COMPLETED

### 9.1 Login Page — Google OAuth Button (M-04)
- **File**: `templates/account/login.html`
- **Current**: Username/password form only
- **Required**: Add "Sign in with Google" button below the form
  - Use django-allauth's Google social login URL
  - Styled as a prominent button with Google icon
  - Separator text: "— or —"

---

## Phase 10 — Reusable Component Patterns — ✅ COMPLETED

### 10.1 Status Badge Component
- **Pattern**: `<span class="badge badge-{{ status }}">{{ status_display }}</span>`
- **Colors**: draft=slate, pending=amber, approved/active=green, rejected=red, completed=blue, in_progress=indigo
- Used across: Needs, Projects, Events, Programs, Expenses, Role Requests

### 10.2 Progress Bar Component
- **Pattern**: `<div class="progress-bar"><div class="progress-fill" style="width:{{ pct }}%"></div></div>`
- **Color thresholds**: 0-25%=red, 25-50%=amber, 50-75%=blue, 75-100%=green
- Used across: Rollup, Pool utilization, Project detail, Program detail, Donor portfolio

### 10.3 Filter Bar Component
- **Pattern**: Horizontal bar with search input + filter dropdowns + sort dropdown + apply button
- Used across: Contributions, Expenses, Audit Log, Role Requests

### 10.4 Modal Component
- **Pattern**: Overlay with card, title, body, confirm/cancel buttons
- **JS**: `data-modal-target` attribute to trigger
- Used for: Project creation confirmation, role request rejection reason, CSV import confirmation

### 10.5 Breadcrumb Component
- **Pattern**: `<nav class="breadcrumb">Home > Module > Current Page</nav>`
- Used on: Project form (from Need), Milestone form (from Project), Program milestone form

### 10.6 Alert/Notification Banner
- **Current**: amber-colored `<li>` elements for Django messages
- **Enhance**: Add icon + dismiss button; color by message level (success=green, warning=amber, error=red, info=blue)

---

## Template File Inventory — Complete List

| # | File | Status | Source Doc |
|---|------|--------|-----------|
| 1 | `templates/base.html` | MODIFY — navbar, hamburger, role switcher, CSS links | Doc 4 §2, M-01, Doc 3 §5b |
| 2 | `templates/dashboard/home.html` | MODIFY — currency toggle, exchange rate | C-02 |
| 3 | `templates/dashboard/project_rollup.html` | MODIFY — alerts, programs section | H-01, Doc 1 §4b |
| 4 | `templates/dashboard/governance_queue.html` | MODIFY — role requests tab, CSV preview | Doc 3 §6, Doc 1 §5a |
| 5 | `templates/funding/contribution_list.html` | MODIFY — search, filter, sort, pagination | C-01 |
| 6 | `templates/funding/expense_list.html` | MODIFY — search, filter, sort, pagination | C-01 pattern |
| 7 | `templates/funding/pool_list.html` | MODIFY — balance cards, progress bars | H-02 |
| 8 | `templates/funding/contribution_form.html` | MODIFY — exchange rate display | C-02 |
| 9 | `templates/stakeholders/profile_form.html` | MODIFY — expanded fields, photo, activity, role request | H-04 |
| 10 | `templates/needs/need_detail.html` | MODIFY — rename button, modal, breadcrumbs | H-03 |
| 11 | `templates/projects/project_detail.html` | MODIFY — program link display | Doc 1 §4b |
| 12 | `templates/projects/project_form.html` | MODIFY — program field, breadcrumbs | Doc 1 §4b, H-03 |
| 13 | `templates/events/event_list.html` | MODIFY — status/type badges, target amount | Doc 1 §4a |
| 14 | `templates/events/event_detail.html` | MODIFY — milestones section, workflow status | Doc 1 §4a |
| 15 | `templates/account/login.html` | MODIFY — Google OAuth button | M-04 |
| 16 | `templates/events/event_form.html` | NEW — create/edit events | Doc 4 §3 |
| 17 | `templates/events/event_milestone_form.html` | NEW — create/edit event milestones | Doc 1 §4a |
| 18 | `templates/programs/program_list.html` | NEW — program listing | Doc 1 §4b |
| 19 | `templates/programs/program_detail.html` | NEW — program detail with milestones | Doc 1 §4b |
| 20 | `templates/programs/program_form.html` | NEW — create/edit programs | Doc 1 §4b |
| 21 | `templates/programs/program_milestone_form.html` | NEW — create/edit program milestones | Doc 1 §4b |
| 22 | `templates/stakeholders/role_request_form.html` | NEW — request additional role | Doc 3 §6 |
| 23 | `templates/stakeholders/role_request_list.html` | NEW — user's own requests | Doc 3 §6 |
| 24 | `templates/core/upload_audit_log.html` | NEW — audit log table | Doc 1 §5b |
| 25 | `static/css/main.css` | NEW — all custom styles | All |

---

## Execution Order

| Step | Templates | Dependencies |
|------|-----------|-------------|
| 1 | `static/css/main.css` — design system (badges, bars, modals, breadcrumbs) | None |
| 2 | `base.html` — navbar + hamburger + role switcher | CSS from step 1 |
| 3 | `contribution_list.html` — filters + pagination | Backend `ContributionFilter` |
| 4 | `pool_list.html` — balance cards + progress bars | Backend pool balance methods |
| 5 | `home.html` — currency toggle + exchange rate | Backend toggle view |
| 6 | `project_rollup.html` — alerts + programs section | Backend stalled logic + program views |
| 7 | `profile_form.html` — expanded + role request button | Backend profile fields + role request views |
| 8 | `role_request_form.html` + `role_request_list.html` | Backend role request views |
| 9 | `governance_queue.html` — role requests tab + CSV preview | Backend CSV verify + role request views |
| 10 | `need_detail.html` — rename button + modal | None |
| 11 | `event_form.html` + `event_detail.html` updates | Backend event create/edit views |
| 12 | `event_milestone_form.html` | Backend event milestone views |
| 13 | All program templates (list, detail, form, milestone form) | Backend program app |
| 14 | `upload_audit_log.html` | Backend audit log view |
| 15 | `login.html` — Google button | Backend OAuth config |
| 16 | `expense_list.html` — filters | Backend ExpenseFilter |
| 17 | `contribution_form.html` — rate display | Backend rate context |
| 18 | `project_detail.html` + `project_form.html` — program link | Backend program field |
