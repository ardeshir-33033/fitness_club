# 🤖 Antigravity AI Agent Guide & Project Memory (Fitness Club Backend)

This file is automatically loaded by Antigravity across all sessions and machines. It preserves the exact project context, user working style, completed phases, and the immediate next steps.

---

## 🛑 STRICT OPERATING RULES FOR AI AGENTS (Crucial - Follow Always)

1. **Hands-On Learning Project:**
   * **DO NOT** edit project code files or execute code changes yourself unless the user explicitly tells you to do so.
   * **ALWAYS** explain:
     1. **WHAT** needs to be done.
     2. **WHY** it is needed (the architectural / engineering rationale).
     3. **HOW** to do it (provide clean, production-ready code snippets and file paths) so the user writes the code themselves.
2. **No Unit Tests:**
   * The user has explicitly decided **NOT** to write automated test files (`tests.py`) for this project. Do not propose or push for unit tests.
3. **Database Indexing:**
   * Database composite indexing on `GymSession` is intentionally **postponed** to Phase 7 (Stress Testing).
4. **Operating System & Environment:**
   * macOS with `zsh`.
   * Virtualenv activation: `source .venv/bin/activate` or prefix commands with `.venv/bin/python`.
   * Python: 3.14+ with Django 6.1, DRF, psycopg (binary), django-filter.

---

## 🏢 Project Context & Engineering Vision

A high-performance, high-concurrency backend for a **Boutique Fitness Club** built with **Django** and **Django REST Framework (DRF)**.

* **Core Business Problem:** 
  Every Sunday at 8:00 PM, weekly sessions open on the mobile app (Flutter). Hundreds of users simultaneously attempt to book limited slots (Private 1-on-1 sessions with capacity = 1, or Group Classes with capacity = 20).
* **Engineering Highlights:**
  * Zero double-booking under extreme concurrency via **Pessimistic Row-Level Locking (`select_for_update()`)** inside **`transaction.atomic()`**.
  * 10-minute temporary seat lock (**`HELD` state**) with automatic TTL expiration.
  * Zero N+1 queries on catalog read endpoints using `select_related('trainer__user')` and dynamic SQL annotations for remaining capacity.
  * Idempotent payment processing with `Idempotency-Key` headers.
  * FIFO Smart Waitlist for fully-booked classes.

---

## 📊 Current Project Status & Roadmap

| Phase | Description | Status |
| :--- | :--- | :--- |
| **Phase 1** | Infrastructure, DRF, `.env`, settings configuration | ✅ **COMPLETED** |
| **Phase 2** | Domain Modeling (`accounts`, `gym_sessions`, `bookings`, `waitlist`), constraints & admin | ✅ **COMPLETED** |
| **Phase 3** | High-performance Read Catalog (`/api/v1/sessions/`, `/api/v1/trainers/`), Serializers & Views | ✅ **COMPLETED** |
| **Phase 4** | **Concurrency & 10-Minute Hold Engine (`POST /api/v1/sessions/{id}/hold/`)** | 🚀 **IN PROGRESS (NEXT STEP)** |
| **Phase 5** | Idempotency & Payment Simulation (`POST /api/v1/bookings/{id}/pay/`) | ⏳ Pending |
| **Phase 6** | Smart Waitlist (FIFO queue & auto-promotion) | ⏳ Pending |
| **Phase 7** | Stress Testing, Locust / Asyncio Concurrency Simulation, Database Indexing | ⏳ Pending |

---

## 🗂️ Completed Architecture & Key Files

* `accounts/models.py`: Custom `User` model with `role` (`CLIENT`, `TRAINER`, `ADMIN`) and `phone_number`.
* `gym_sessions/models.py`:
  * `Trainer`: `user` (1-to-1), `specialty`, `bio`, `is_active`.
  * `GymSession`: `trainer`, `title`, `session_type` (`PRIVATE_1ON1`, `GROUP_CLASS`), `starts_at`, `ends_at`, `max_capacity`, `price`, `status`, check constraints, and `get_available_capacity()`.
* `bookings/models.py`:
  * `Booking`: `user`, `session`, `status` (`HELD`, `CONFIRMED`, `CANCELLED`, `EXPIRED`), `created_at`, `expires_at` (10-minute hold), `idempotency_key`.
  * Unique constraint: A user cannot have multiple active (`HELD` or `CONFIRMED`) bookings for the same session.
* `waitlist/models.py`: `WaitlistEntry` with FIFO ordering for sold-out classes.
* `gym_sessions/serializers.py`:
  * `TrainerSummarySerializer` & `TrainerDetailSerializer` (with `user.get_full_name` source).
  * `GymSessionListSerializer` & `GymSessionDetailSerializer` (with dynamic `available_capacity`).
* `gym_sessions/views.py`:
  * `TrainerReadOnlyViewSet`: search, ordering, `select_related('user')`.
  * `GymSessionReadOnlyViewSet`: `select_related('trainer__user')`, conditional `Count` on active bookings (`CONFIRMED` or unexpired `HELD`), dynamic `available_capacity = max_capacity - active_bookings_count`.
* `gym_sessions/urls.py` & `config/urls.py`:
  * All read catalog endpoints active under `/api/v1/sessions/` and `/api/v1/trainers/`.

---

## 🎯 EXACT NEXT TASK: Starting Phase 4 (The 10-Minute Hold Engine)

When resuming, the immediate task is to implement the **Seat Hold Endpoint**:

1. **Endpoint:** `POST /api/v1/sessions/{id}/hold/` (requires `IsAuthenticated`).
2. **Pessimistic Locking Mechanism:**
   ```python
   with transaction.atomic():
       # Lock the session row exclusively in PostgreSQL:
       session = GymSession.objects.select_for_update().get(id=session_id)
       
       # Calculate real-time active bookings under the lock:
       # active = CONFIRMED + unexpired HELD
       # If active >= session.max_capacity -> return HTTP 409 Conflict
       
       # Otherwise create Booking with status=BookingStatus.HELD and expires_at = now + 10 mins
       # Return HTTP 201 Created with booking ID and expires_at countdown
   ```
3. **Background Expiration Sweep:**
   * Build a management command (or background task) to sweep holds where `status == HELD` and `expires_at < timezone.now()`, marking them `EXPIRED`.
