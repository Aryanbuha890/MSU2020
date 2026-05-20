# MSU VISION 2020 — Frontend to Backend Connection Map

This document connects every single one of the 10 Frontend HTML template phases to their exact Backend counterparts. Since the HTML files have already been created, the Backend Developer must ensure that the corresponding Models, Views, URLs, and Context Variables are built to make the frontend function properly.

---

## 🔗 Phase 1: Global Layout & Navigation
| Frontend Template | Feature | Required Backend Implementation |
| :--- | :--- | :--- |
| `base.html` | **Per-Persona Nav** | **Context Processor:** `apps.core.context_processors.persona_nav_items`. Must return a `nav_items` list based on the user's active personas (intersection logic). |
| `base.html` | **Role Switcher** | **View & URL:** A POST view `switch_role` in `apps.dashboard.views` to change the `active_persona` stored in the session. |

---

## 🔗 Phase 2: Funding Module Templates
| Frontend Template | Feature | Required Backend Implementation |
| :--- | :--- | :--- |
| `contribution_list.html`<br>`expense_list.html` | **Interactive Tables** | **Views & Filters:** Convert `ContributionListView` and `ExpenseListView` to use `django-filter` (`FilterView`). Must supply `filter.form` to the template. |
| `pool_list.html` | **Rich Pool Cards** | **Model Methods:** Add `total_collected_usd()`, `total_allocated_usd()`, and `utilization_percent()` to the `FundPool` model. Supply to template context. |
| `contribution_form.html` | **Exchange Rate** | **Model & Context:** Add `exchange_rate_used` to `Contribution` model. Pass current API exchange rate to the template context for JS preview. |

---

## 🔗 Phase 3: Dashboard Templates
| Frontend Template | Feature | Required Backend Implementation |
| :--- | :--- | :--- |
| `home.html` | **Currency Toggle** | **View:** A POST view `toggle_currency` to flip session state. `HomeView` must return `scorecard` amounts dynamically converted based on the session flag. |
| `project_rollup.html` | **Smart Alerts** | **View Logic:** `ProjectRollupView` must annotate `is_stalled = True` if project is in-progress and all milestones are 0% for 14+ days. |
| `governance_queue.html` | **CSV Preview & Roles** | **Views:** Add a 2-step process (`governance_csv_preview` and `governance_csv_confirm`). Pass `pending_role_requests` context to the view. |

---

## 🔗 Phase 4: Profile & Roles
| Frontend Template | Feature | Required Backend Implementation |
| :--- | :--- | :--- |
| `profile_form.html` | **Rich Profiles** | **Models:** Expand `UserProfile` with `batch_year`, `bio`, `department`, `photo`, `linkedin_url`. Update `UserProfileForm`. |
| `role_request_form.html`<br>`role_request_list.html` | **Role Requests UI** | **Models & Views:** Create new `UserRoleRequest` model. Build `RoleRequestCreateView`, `RoleRequestListView`, and `role_request_approve`/`reject` views. |

---

## 🔗 Phase 5: Event Templates
| Frontend Template | Feature | Required Backend Implementation |
| :--- | :--- | :--- |
| `event_form.html` | **Create Events** | **Views:** New `EventCreateView` and `EventUpdateView` in `apps.events`. Restricted to Governance/Admin. |
| `event_detail.html`<br>`event_milestone_form.html` | **Event Milestones** | **Models & Views:** Create `EventMilestone` model. Add `event_milestone_complete` view to handle proof uploads. Add `is_fundraising` flag to `Event`. |

---

## 🔗 Phase 6: Program Management (NEW APP)
| Frontend Template | Feature | Required Backend Implementation |
| :--- | :--- | :--- |
| `program_list.html`<br>`program_detail.html` | **Program Tracking** | **Models:** Create new `apps.programs` app. Build `Program` and `ProgramMilestone` models. Link them to `FundPool`. |
| `program_form.html`<br>`program_milestone_form.html`| **Program CRUD** | **Views:** Build standard Create/Update views restricted to Governance Team. Include `program_milestone_tranche_release` POST view. |

---

## 🔗 Phase 7: Upload Audit Log
| Frontend Template | Feature | Required Backend Implementation |
| :--- | :--- | :--- |
| `upload_audit_log.html` | **Audit Table** | **Models & Views:** Create `UploadAuditLog` model to track MIME/ClamAV scans. Create `UploadAuditLogListView` (read-only for Auditor/Gov, full for Admin). |

---

## 🔗 Phase 8: Project UX
| Frontend Template | Feature | Required Backend Implementation |
| :--- | :--- | :--- |
| `need_detail.html` | **Guiding Modal** | **None:** This is purely a frontend JS/HTML addition. Button opens modal, confirm redirects to standard project creation URL. |
| `project_form.html`<br>`project_detail.html` | **Program Linking** | **Model:** Add a `program = ForeignKey(Program)` to the `Project` model so incubator projects can link to their parent program. |

---

## 🔗 Phase 9: Account & Auth
| Frontend Template | Feature | Required Backend Implementation |
| :--- | :--- | :--- |
| `login.html` | **Google OAuth** | **Settings:** Configure `django-allauth` in `config/settings.py` with valid Google Client ID/Secret. Add post-login signal to link email to existing profile. |

---

## 🔗 Phase 10: Reusable Components
| Frontend Template | Feature | Required Backend Implementation |
| :--- | :--- | :--- |
| All templates (Badges, Alerts, Progress Bars, Modals) | **UI Polish** | **None:** The backend only needs to ensure the Django Messaging framework (`django.contrib.messages`) is used consistently across views (e.g., `messages.success()`) so the UI alerts trigger properly. |
