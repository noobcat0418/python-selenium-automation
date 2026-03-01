"""FastAPI mock authentication server for E2E testing."""

from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Form, Request, Response
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.auth import (
    check_rate_limit,
    create_access_token,
    create_short_lived_token,
    decode_token,
    record_failed_attempt,
    reset_failed_attempts,
)
from app.models import reset_stores, users
from app.oauth import (
    generate_oauth_state,
    get_or_create_oauth_user,
    get_provider_config,
    validate_oauth_state,
)

BASE_DIR = Path(__file__).resolve().parent
app = FastAPI(title="Auth E2E Test Server", docs_url=None, redoc_url=None)

app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_current_user(request: Request) -> Optional[dict]:
    """Extract user from JWT cookie. Returns payload or None."""
    token = request.cookies.get("access_token")
    if not token:
        return None
    return decode_token(token)


def _require_auth(request: Request) -> Optional[RedirectResponse]:
    """Return a redirect to /login if user is not authenticated."""
    user = _get_current_user(request)
    if user is None:
        next_url = request.url.path
        return RedirectResponse(f"/login?next={next_url}", status_code=302)
    return None


# ---------------------------------------------------------------------------
# Public routes
# ---------------------------------------------------------------------------

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    user = _get_current_user(request)
    if user:
        return RedirectResponse("/dashboard", status_code=302)
    return RedirectResponse("/login", status_code=302)


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, error: str = "", next: str = "/dashboard"):
    user = _get_current_user(request)
    if user:
        return RedirectResponse("/dashboard", status_code=302)
    return templates.TemplateResponse("login.html", {
        "request": request,
        "error": error,
        "next": next,
    })


@app.post("/login")
async def login_submit(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    next: str = Form("/dashboard"),
):
    # Check rate limit
    is_locked, lock_msg = check_rate_limit(email)
    if is_locked:
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": lock_msg,
            "next": next,
        }, status_code=429)

    # Validate credentials
    user = users.get(email)
    if user is None or not user.verify_password(password):
        is_now_locked, fail_msg = record_failed_attempt(email)
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": fail_msg or "Invalid email or password.",
            "next": next,
        }, status_code=401)

    # Successful login
    reset_failed_attempts(email)
    token = create_access_token(email=user.email, name=user.name, provider=user.provider)
    response = RedirectResponse(next, status_code=302)
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        samesite="lax",
        max_age=1800,
    )
    return response


@app.get("/logout")
async def logout():
    response = RedirectResponse("/login", status_code=302)
    response.delete_cookie("access_token")
    return response


# ---------------------------------------------------------------------------
# Protected routes
# ---------------------------------------------------------------------------

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    redirect = _require_auth(request)
    if redirect:
        return redirect
    user = _get_current_user(request)
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "user": user,
    })


@app.get("/profile", response_class=HTMLResponse)
async def profile(request: Request):
    redirect = _require_auth(request)
    if redirect:
        return redirect
    user = _get_current_user(request)
    return templates.TemplateResponse("profile.html", {
        "request": request,
        "user": user,
    })


# ---------------------------------------------------------------------------
# Mock OAuth routes
# ---------------------------------------------------------------------------

@app.get("/oauth/{provider}/login")
async def oauth_start(provider: str):
    config = get_provider_config(provider)
    if not config:
        return JSONResponse({"error": "Unknown provider"}, status_code=400)
    state = generate_oauth_state(provider)
    return RedirectResponse(f"/oauth/{provider}/consent?state={state}", status_code=302)


@app.get("/oauth/{provider}/consent", response_class=HTMLResponse)
async def oauth_consent(request: Request, provider: str, state: str = ""):
    config = get_provider_config(provider)
    if not config:
        return JSONResponse({"error": "Unknown provider"}, status_code=400)
    return templates.TemplateResponse("oauth_consent.html", {
        "request": request,
        "provider": config,
        "provider_key": provider,
        "state": state,
    })


@app.post("/oauth/{provider}/callback")
async def oauth_callback(
    provider: str,
    state: str = Form(""),
    action: str = Form("allow"),
):
    # User denied
    if action == "deny":
        return RedirectResponse("/login?error=OAuth+login+cancelled", status_code=302)

    # Validate state
    oauth_state = validate_oauth_state(state)
    if not oauth_state or oauth_state.provider != provider:
        return RedirectResponse("/login?error=Invalid+OAuth+state", status_code=302)

    # Create/get user and log them in
    user = get_or_create_oauth_user(provider)
    token = create_access_token(
        email=user.email, name=user.name, provider=user.provider
    )
    response = RedirectResponse("/dashboard", status_code=302)
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        samesite="lax",
        max_age=1800,
    )
    return response


# ---------------------------------------------------------------------------
# Test helper API endpoints
# ---------------------------------------------------------------------------

@app.get("/api/session-info")
async def session_info(request: Request):
    user = _get_current_user(request)
    if not user:
        return JSONResponse({"authenticated": False}, status_code=401)
    return JSONResponse({
        "authenticated": True,
        "email": user.get("sub"),
        "name": user.get("name"),
        "provider": user.get("provider", "local"),
    })


@app.post("/api/reset")
async def reset_state():
    """Reset all server state — for test isolation."""
    reset_stores()
    return JSONResponse({"status": "reset"})


@app.post("/api/set-short-token")
async def set_short_token(
    request: Request,
    email: str = Form(...),
    seconds: int = Form(5),
):
    """Set a short-lived token cookie — for session expiration tests."""
    user = users.get(email)
    if not user:
        return JSONResponse({"error": "User not found"}, status_code=404)
    token = create_short_lived_token(email=user.email, name=user.name, seconds=seconds)
    response = JSONResponse({"status": "ok", "expires_in": seconds})
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        samesite="lax",
        max_age=seconds,
    )
    return response


@app.get("/health")
async def health():
    return {"status": "ok"}
