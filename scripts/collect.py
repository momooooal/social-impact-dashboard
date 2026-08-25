#!/usr/bin/env python3
"""Collect Facebook, Instagram and Threads insights into one GitHub-Pages-friendly JSON file.

Tokens are read only from environment variables named by config/accounts.json.
The collector is deliberately tolerant of metric deprecations: metrics are queried separately
where practical, and unsupported metrics are recorded as warnings instead of aborting the run.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import requests

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = ROOT / "config" / "accounts.json"
DEFAULT_OUTPUT = ROOT / "data" / "analytics.json"
TIMEOUT = 35
SESSION = requests.Session()
SESSION.headers.update({"User-Agent": "social-impact-dashboard/1.0"})


def iso_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def date_utc(days_ago: int = 0) -> str:
    return (datetime.now(timezone.utc).date() - timedelta(days=days_ago)).isoformat()


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    tmp.replace(path)


def safe_num(value: Any) -> float:
    if isinstance(value, bool):
        return float(value)
    if isinstance(value, (int, float)):
        return value
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return 0
    return 0


def metric_scalar(insight: Dict[str, Any]) -> Any:
    if insight.get("total_value") is not None:
        tv = insight["total_value"]
        return tv.get("value") if isinstance(tv, dict) else tv
    values = insight.get("values") or []
    if not values:
        return None
    last = values[-1]
    return last.get("value") if isinstance(last, dict) else last


class CollectorError(RuntimeError):
    pass


class API:
    def __init__(self, warnings: List[Dict[str, Any]]):
        self.warnings = warnings

    def get(self, url: str, params: Dict[str, Any], account_key: str, purpose: str, soft: bool = False) -> Optional[Dict[str, Any]]:
        for attempt in range(3):
            try:
                r = SESSION.get(url, params=params, timeout=TIMEOUT)
                payload = r.json() if r.content else {}
            except (requests.RequestException, ValueError) as e:
                if attempt < 2:
                    time.sleep(2 ** attempt)
                    continue
                if soft:
                    self.warn(account_key, purpose, f"network/json error: {e}")
                    return None
                raise CollectorError(f"{purpose}: {e}") from e

            if r.ok:
                return payload

            err = payload.get("error", {}) if isinstance(payload, dict) else {}
            message = err.get("message") or f"HTTP {r.status_code}"
            transient = bool(err.get("is_transient")) or r.status_code >= 500 or r.status_code == 429
            if transient and attempt < 2:
                time.sleep(2 ** attempt)
                continue
            if soft:
                self.warn(account_key, purpose, message, code=err.get("code"))
                return None
            raise CollectorError(f"{purpose}: {message}")
        return None

    def paginate(self, url: str, params: Dict[str, Any], account_key: str, purpose: str, max_items: int) -> List[Dict[str, Any]]:
        items: List[Dict[str, Any]] = []
        next_url: Optional[str] = url
        next_params: Optional[Dict[str, Any]] = dict(params)
        while next_url and len(items) < max_items:
            payload = self.get(next_url, next_params or {}, account_key, purpose, soft=True)
            if not payload:
                break
            batch = payload.get("data") or []
            if not isinstance(batch, list):
                break
            items.extend(batch)
            next_url = (payload.get("paging") or {}).get("next")
            next_params = None  # next URL already contains cursor/token
            if not next_url or not batch:
                break
        return items[:max_items]

    def warn(self, account_key: str, purpose: str, message: str, code: Any = None) -> None:
        self.warnings.append({
            "time": iso_now(), "account_key": account_key, "purpose": purpose,
            "message": message, "code": code
        })


def normalize_daily_value(value: Any, canonical: str, row: Dict[str, Any]) -> None:
    if isinstance(value, dict):
        # Instagram follows_and_unfollows and some breakdown metrics return nested objects.
        lowered = {str(k).lower(): v for k, v in value.items()}
        if canonical == "follows_and_unfollows":
            row["follows"] = safe_num(lowered.get("follows", lowered.get("follow", 0)))
            row["unfollows"] = safe_num(lowered.get("unfollows", lowered.get("unfollow", 0)))
            return
        # Do not flatten demographics into a scalar.
        return
    row[canonical] = safe_num(value)


def merge_daily_rows(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    merged: Dict[Tuple[str, str, str], Dict[str, Any]] = {}
    for row in rows:
        key = (row.get("date", ""), row.get("platform", ""), row.get("account_key", ""))
        target = merged.setdefault(key, {"date": key[0], "platform": key[1], "account_key": key[2]})
        for k, v in row.items():
            if k in {"date", "platform", "account_key"}:
                continue
            if isinstance(v, (int, float)):
                target[k] = v
            elif v is not None:
                target[k] = v
    return sorted(merged.values(), key=lambda x: (x.get("date", ""), x.get("platform", ""), x.get("account_key", "")))


def account_insights(api: API, base: str, account_id: str, token: str, key: str, platform: str,
                     metrics: Dict[str, str], since: str, until: str, period: str = "day") -> List[Dict[str, Any]]:
    by_date: Dict[str, Dict[str, Any]] = {}
    for vendor_metric, canonical in metrics.items():
        payload = api.get(
            f"{base}/{account_id}/insights",
            {"metric": vendor_metric, "period": period, "since": since, "until": until, "access_token": token},
            key, f"{platform} account metric {vendor_metric}", soft=True
        )
        if not payload:
            continue
        for insight in payload.get("data") or []:
            values = insight.get("values") or []
            if values:
                for point in values:
                    end = point.get("end_time") or until
                    d = str(end)[:10]
                    row = by_date.setdefault(d, {"date": d, "platform": platform, "account_key": key})
                    normalize_daily_value(point.get("value"), canonical, row)
            elif insight.get("total_value") is not None:
                # total_value may represent the whole selected range. Only store it as a daily point
                # when the request covers one day; otherwise the dashboard would falsely imply timing.
                if since == until:
                    row = by_date.setdefault(until, {"date": until, "platform": platform, "account_key": key})
                    normalize_daily_value(metric_scalar(insight), canonical, row)
    return list(by_date.values())


def fetch_post_metric_candidates(api: API, base: str, post_id: str, token: str, key: str,
                                 platform: str, candidates: Dict[str, str]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for vendor_metric, canonical in candidates.items():
        payload = api.get(f"{base}/{post_id}/insights", {"metric": vendor_metric, "access_token": token},
                          key, f"{platform} post metric {vendor_metric}", soft=True)
        if not payload:
            continue
        data = payload.get("data") or []
        if not data:
            continue
        value = metric_scalar(data[0])
        if isinstance(value, dict):
            continue
        out[canonical] = safe_num(value)
    return out


def collect_facebook(api: API, cfg: Dict[str, Any], acct: Dict[str, Any], token: str) -> Tuple[Dict[str, Any], List[Dict[str, Any]], List[Dict[str, Any]]]:
    version = cfg.get("meta_api_version", "v26.0")
    base = f"https://graph.facebook.com/{version}"
    aid, key = acct["id"], acct["key"]
    profile = api.get(f"{base}/{aid}", {
        "fields": "id,name,username,followers_count,fan_count,picture.type(large)", "access_token": token
    }, key, "facebook profile", soft=False) or {}
    account = {
        "key": key, "platform": "facebook", "id": aid, "label": acct.get("label") or profile.get("name") or key,
        "name": profile.get("name") or acct.get("label") or key, "username": profile.get("username"),
        "followers": safe_num(profile.get("followers_count") or profile.get("fan_count")),
        "avatar_url": (((profile.get("picture") or {}).get("data") or {}).get("url")), "status": "ok"
    }
    since = date_utc(int(cfg.get("lookback_days", 90)))
    until = date_utc(0)
    metrics = {
        "page_media_view": "views",
        "page_total_media_view_unique": "reach",
        "page_views_total": "profile_views",
        "page_post_engagements": "interactions",
        "page_daily_follows": "follows",
        "page_video_views": "video_views",
        "page_video_view_time": "video_view_time"
    }
    daily = account_insights(api, base, aid, token, key, "facebook", metrics, since, until)

    post_since = date_utc(int(cfg.get("post_lookback_days", 365)))
    raw_posts = api.paginate(f"{base}/{aid}/posts", {
        "fields": "id,message,created_time,permalink_url,shares,reactions.limit(0).summary(true),comments.limit(0).summary(true),attachments{media_type,type}",
        "since": post_since, "limit": 100, "access_token": token
    }, key, "facebook posts", int(cfg.get("max_posts_per_account", 120)))
    posts = []
    candidates = {
        "post_media_view": "views",
        "post_total_media_view_unique": "reach",
        "post_clicks": "clicks"
    }
    for p in raw_posts:
        reaction_count = safe_num((((p.get("reactions") or {}).get("summary") or {}).get("total_count")))
        comments_count = safe_num((((p.get("comments") or {}).get("summary") or {}).get("total_count")))
        shares = safe_num((p.get("shares") or {}).get("count"))
        att = ((p.get("attachments") or {}).get("data") or [{}])[0]
        metrics_post = fetch_post_metric_candidates(api, base, p["id"], token, key, "facebook", candidates)
        row = {
            "id": p["id"], "platform": "facebook", "account_key": key,
            "timestamp": p.get("created_time"), "text": p.get("message") or "",
            "permalink": p.get("permalink_url"), "media_type": att.get("media_type") or att.get("type") or "POST",
            "likes": reaction_count, "comments": comments_count, "shares": shares,
        }
        row.update(metrics_post)
        row["interactions"] = reaction_count + comments_count + shares + safe_num(row.get("clicks"))
        posts.append(row)
    return account, daily, posts


def collect_instagram(api: API, cfg: Dict[str, Any], acct: Dict[str, Any], token: str) -> Tuple[Dict[str, Any], List[Dict[str, Any]], List[Dict[str, Any]]]:
    version = cfg.get("meta_api_version", "v26.0")
    base = f"https://graph.instagram.com/{version}"
    aid, key = acct["id"], acct["key"]
    profile = api.get(f"{base}/{aid}", {
        "fields": "id,username,name,followers_count,media_count,profile_picture_url", "access_token": token
    }, key, "instagram profile", soft=False) or {}
    account = {
        "key": key, "platform": "instagram", "id": aid, "label": acct.get("label") or profile.get("username") or key,
        "name": profile.get("name") or profile.get("username") or acct.get("label") or key,
        "username": profile.get("username"), "followers": safe_num(profile.get("followers_count")),
        "content_count": safe_num(profile.get("media_count")), "avatar_url": profile.get("profile_picture_url"), "status": "ok"
    }
    since = date_utc(int(cfg.get("lookback_days", 90)))
    until = date_utc(0)
    metrics = {
        "views": "views", "reach": "reach", "profile_views": "profile_views",
        "accounts_engaged": "accounts_engaged", "total_interactions": "interactions",
        "follows_and_unfollows": "follows_and_unfollows", "follower_count": "followers"
    }
    daily = account_insights(api, base, aid, token, key, "instagram", metrics, since, until)
    raw_posts = api.paginate(f"{base}/{aid}/media", {
        "fields": "id,caption,media_type,media_product_type,permalink,timestamp,like_count,comments_count,thumbnail_url",
        "limit": 100, "access_token": token
    }, key, "instagram media", int(cfg.get("max_posts_per_account", 120)))
    cutoff = datetime.now(timezone.utc) - timedelta(days=int(cfg.get("post_lookback_days", 365)))
    posts = []
    for p in raw_posts:
        ts = p.get("timestamp")
        try:
            dt = datetime.fromisoformat(ts.replace("Z", "+00:00")) if ts else datetime.now(timezone.utc)
        except ValueError:
            dt = datetime.now(timezone.utc)
        if dt < cutoff:
            continue
        # Instagram supports comma-separated media metrics. Use one request per media object
        # rather than N requests per metric, which keeps daily API volume reasonable.
        media_kind = str(p.get("media_product_type") or p.get("media_type") or "").upper()
        if "REEL" in media_kind:
            metric_names = ["views", "reach", "likes", "comments", "shares", "saved", "total_interactions",
                            "ig_reels_video_view_total_time", "ig_reels_avg_watch_time"]
        else:
            metric_names = ["views", "reach", "likes", "comments", "shares", "saved", "total_interactions",
                            "follows", "profile_visits"]
        payload = api.get(
            f"{base}/{p['id']}/insights",
            {"metric": ",".join(metric_names), "access_token": token},
            key, "instagram media insights", soft=True
        ) or {}
        metrics_post: Dict[str, Any] = {}
        mapping = {
            "views": "views", "reach": "reach", "likes": "likes", "comments": "comments",
            "shares": "shares", "saved": "saves", "total_interactions": "interactions",
            "follows": "follows", "profile_visits": "profile_views",
            "ig_reels_video_view_total_time": "video_view_time", "ig_reels_avg_watch_time": "avg_watch_time"
        }
        for insight in payload.get("data") or []:
            value = metric_scalar(insight)
            if not isinstance(value, dict) and value is not None and insight.get("name") in mapping:
                metrics_post[mapping[insight["name"]]] = safe_num(value)
        # If a media type rejects the combined request, retain core performance with a small
        # fallback set instead of exploding into a dozen API calls.
        if not payload.get("data"):
            for vendor_metric, canonical in {"views": "views", "reach": "reach", "shares": "shares", "saved": "saves"}.items():
                single = api.get(
                    f"{base}/{p['id']}/insights", {"metric": vendor_metric, "access_token": token},
                    key, f"instagram media fallback {vendor_metric}", soft=True
                ) or {}
                arr = single.get("data") or []
                if arr:
                    value = metric_scalar(arr[0])
                    if not isinstance(value, dict) and value is not None:
                        metrics_post[canonical] = safe_num(value)
        row = {
            "id": p["id"], "platform": "instagram", "account_key": key, "timestamp": ts,
            "text": p.get("caption") or "", "permalink": p.get("permalink"),
            "media_type": p.get("media_product_type") or p.get("media_type") or "POST",
            "likes": safe_num(p.get("like_count")), "comments": safe_num(p.get("comments_count"))
        }
        row.update(metrics_post)
        # Keep field counts when insights omit the equivalent metric.
        row["likes"] = max(safe_num(row.get("likes")), safe_num(p.get("like_count")))
        row["comments"] = max(safe_num(row.get("comments")), safe_num(p.get("comments_count")))
        if not row.get("interactions"):
            row["interactions"] = sum(safe_num(row.get(k)) for k in ("likes", "comments", "shares", "saves"))
        posts.append(row)
    return account, daily, posts


def collect_threads(api: API, cfg: Dict[str, Any], acct: Dict[str, Any], token: str) -> Tuple[Dict[str, Any], List[Dict[str, Any]], List[Dict[str, Any]]]:
    version = cfg.get("threads_api_version", "v1.0")
    base = f"https://graph.threads.net/{version}"
    aid, key = acct.get("id") or "me", acct["key"]
    profile = api.get(f"{base}/{aid}", {
        "fields": "id,username,name,threads_profile_picture_url,threads_biography", "access_token": token
    }, key, "threads profile", soft=False) or {}
    resolved_id = profile.get("id") or aid
    account = {
        "key": key, "platform": "threads", "id": resolved_id, "label": acct.get("label") or profile.get("username") or key,
        "name": profile.get("name") or profile.get("username") or acct.get("label") or key,
        "username": profile.get("username"), "followers": 0,
        "avatar_url": profile.get("threads_profile_picture_url"), "status": "ok"
    }
    since = date_utc(int(cfg.get("lookback_days", 90)))
    until = date_utc(0)
    # Threads uses /threads_insights for account-level metrics (post metrics use /insights).
    daily_by_date: Dict[str, Dict[str, Any]] = {}
    metrics = {
        "views": "views", "followers_count": "followers"
    }
    for vendor_metric, canonical in metrics.items():
        payload = api.get(
            f"{base}/{resolved_id}/threads_insights",
            {"metric": vendor_metric, "since": since, "until": until, "access_token": token},
            key, f"threads account metric {vendor_metric}", soft=True
        ) or {}
        for insight in payload.get("data") or []:
            for point in insight.get("values") or []:
                d = str(point.get("end_time") or until)[:10]
                row = daily_by_date.setdefault(d, {"date": d, "platform": "threads", "account_key": key})
                normalize_daily_value(point.get("value"), canonical, row)

    # Interaction metrics are commonly returned as total_value for the selected interval.
    # Capture a one-day interval (yesterday -> today) so scheduled runs create a truthful
    # daily history instead of assigning a 90-day total to one date.
    day_until = date_utc(0)
    day_since = date_utc(1)
    daily_row = daily_by_date.setdefault(day_since, {"date": day_since, "platform": "threads", "account_key": key})
    for vendor_metric, canonical in {
        "likes": "likes", "replies": "replies", "reposts": "reposts",
        "quotes": "quotes", "clicks": "clicks"
    }.items():
        payload = api.get(
            f"{base}/{resolved_id}/threads_insights",
            {"metric": vendor_metric, "since": day_since, "until": day_until, "access_token": token},
            key, f"threads account metric {vendor_metric}", soft=True
        ) or {}
        data_points = payload.get("data") or []
        if data_points:
            value = metric_scalar(data_points[0])
            if not isinstance(value, dict) and value is not None:
                daily_row[canonical] = safe_num(value)
    daily_row["interactions"] = sum(safe_num(daily_row.get(k)) for k in ("likes", "replies", "reposts", "quotes"))
    daily = list(daily_by_date.values())
    if daily:
        f = [r.get("followers") for r in sorted(daily, key=lambda r: r.get("date", "")) if r.get("followers") is not None]
        if f:
            account["followers"] = safe_num(f[-1])
    raw_posts = api.paginate(f"{base}/{resolved_id}/threads", {
        "fields": "id,media_product_type,media_type,permalink,username,text,timestamp,shortcode,is_quote_post,has_replies",
        "since": date_utc(int(cfg.get("post_lookback_days", 365))), "limit": 50, "access_token": token
    }, key, "threads posts", int(cfg.get("max_posts_per_account", 120)))
    posts = []
    for p in raw_posts:
        insight = api.get(f"{base}/{p['id']}/insights", {
            "metric": "views,likes,replies,reposts,quotes,shares", "access_token": token
        }, key, "threads post insights", soft=True) or {}
        vals: Dict[str, Any] = {}
        for metric in insight.get("data") or []:
            value = metric_scalar(metric)
            if not isinstance(value, dict):
                vals[metric.get("name")] = safe_num(value)
        row = {
            "id": p["id"], "platform": "threads", "account_key": key, "timestamp": p.get("timestamp"),
            "text": p.get("text") or "", "permalink": p.get("permalink"), "media_type": p.get("media_type") or "TEXT_POST",
            "views": safe_num(vals.get("views")), "likes": safe_num(vals.get("likes")),
            "replies": safe_num(vals.get("replies")), "reposts": safe_num(vals.get("reposts")),
            "quotes": safe_num(vals.get("quotes")), "shares": safe_num(vals.get("shares")),
            "is_quote_post": bool(p.get("is_quote_post"))
        }
        row["interactions"] = sum(safe_num(row.get(k)) for k in ("likes", "replies", "reposts", "quotes", "shares"))
        posts.append(row)
    return account, daily, posts


def merge_history(old: Dict[str, Any], fresh_accounts: List[Dict[str, Any]], fresh_daily: List[Dict[str, Any]], fresh_posts: List[Dict[str, Any]], warnings: List[Dict[str, Any]], project: Dict[str, Any]) -> Dict[str, Any]:
    old_daily = old.get("daily") or []
    old_posts = old.get("posts") or []

    daily_map = {(r.get("date"), r.get("platform"), r.get("account_key")): r for r in old_daily}
    for r in fresh_daily:
        key = (r.get("date"), r.get("platform"), r.get("account_key"))
        daily_map[key] = {**daily_map.get(key, {}), **r}

    post_map = {(r.get("platform"), r.get("account_key"), r.get("id")): r for r in old_posts}
    for r in fresh_posts:
        key = (r.get("platform"), r.get("account_key"), r.get("id"))
        post_map[key] = {**post_map.get(key, {}), **r}

    account_map = {(a.get("platform"), a.get("key")): a for a in (old.get("accounts") or [])}
    for a in fresh_accounts:
        account_map[(a.get("platform"), a.get("key"))] = {**account_map.get((a.get("platform"), a.get("key")), {}), **a}

    logs = (old.get("collection_log") or [])[-59:]
    logs.append({"time": iso_now(), "accounts_ok": len(fresh_accounts), "daily_rows": len(fresh_daily), "posts": len(fresh_posts), "warnings": len(warnings)})

    return {
        "meta": {
            "schema_version": 1, "generated_at": iso_now(), "source": "meta-api",
            "project": project, "warning_count": len(warnings),
            "notes": [
                "跨平台的 views/reach 定義並不完全相同，儀表板會分平台呈現並提供合併『曝光/觀看』指標。",
                "貼文互動數多為目前累積值，歸因到貼文發布日；不代表互動實際發生在該日。"
            ]
        },
        "accounts": sorted(account_map.values(), key=lambda x: (x.get("platform", ""), x.get("key", ""))),
        "daily": sorted(daily_map.values(), key=lambda x: (x.get("date", ""), x.get("platform", ""), x.get("account_key", ""))),
        "posts": sorted(post_map.values(), key=lambda x: x.get("timestamp") or "", reverse=True),
        "warnings": warnings[-300:],
        "collection_log": logs
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default=str(DEFAULT_CONFIG))
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    parser.add_argument("--demo-fallback", action="store_true", help="Keep existing demo data if no account can be collected")
    args = parser.parse_args()

    config_path, output_path = Path(args.config), Path(args.output)
    cfg = load_json(config_path, {})
    if not cfg.get("accounts"):
        print("No accounts configured.", file=sys.stderr)
        return 2

    old = load_json(output_path, {})
    warnings: List[Dict[str, Any]] = []
    api = API(warnings)
    accounts: List[Dict[str, Any]] = []
    daily: List[Dict[str, Any]] = []
    posts: List[Dict[str, Any]] = []

    for acct in cfg.get("accounts", []):
        if not acct.get("enabled", True):
            continue
        key = acct.get("key") or "unknown"
        token_env = acct.get("token_env")
        token = os.getenv(token_env or "", "")
        if not token:
            api.warn(key, "configuration", f"Missing GitHub secret/environment variable: {token_env}")
            continue
        try:
            platform = str(acct.get("platform", "")).lower()
            if platform == "facebook":
                a, d, p = collect_facebook(api, cfg, acct, token)
            elif platform == "instagram":
                a, d, p = collect_instagram(api, cfg, acct, token)
            elif platform == "threads":
                a, d, p = collect_threads(api, cfg, acct, token)
            else:
                api.warn(key, "configuration", f"Unsupported platform: {platform}")
                continue
            accounts.append(a); daily.extend(d); posts.extend(p)
            print(f"OK {key}: daily={len(d)} posts={len(p)}")
        except Exception as e:
            api.warn(key, "collector", str(e))
            print(f"WARN {key}: {e}", file=sys.stderr)

    if not accounts and args.demo_fallback and old.get("meta", {}).get("source") == "demo":
        old["warnings"] = warnings
        old["meta"]["generated_at"] = iso_now()
        old["meta"]["warning_count"] = len(warnings)
        save_json(output_path, old)
        print("No live account collected; retained demo data.")
        return 0

    # Never merge real API data with bundled demonstration values.
    if accounts and old.get("meta", {}).get("source") == "demo":
        old = {}
    merged = merge_history(old, accounts, merge_daily_rows(daily), posts, warnings, cfg.get("project") or {})
    save_json(output_path, merged)
    print(f"Saved {output_path}: accounts={len(accounts)}, daily={len(daily)}, posts={len(posts)}, warnings={len(warnings)}")
    return 0 if accounts else 1


if __name__ == "__main__":
    raise SystemExit(main())
