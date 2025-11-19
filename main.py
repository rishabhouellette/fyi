"""FYI Uploader main entry point with runtime patches.

This module loads the last known-good compiled UI implementation from
``__pycache__/main_legacy.cpython-313.pyc`` and then applies the latest
scheduler improvements (queue preservation, concurrency, and duration
tracking) dynamically. This approach lets us keep the mature UI surface
while iterating on the scheduling logic entirely in Python source.
"""

from __future__ import annotations

import importlib.machinery
import importlib.util
import logging
import queue
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from pathlib import Path
from typing import List

from tkinter import messagebox as _tk_messagebox

_ORIGINAL_PYC = Path(__file__).with_name("__pycache__") / "main_legacy.cpython-313.pyc"
_MODULE_NAME = "_fyi_uploader_legacy"


def _load_original_module():
    if not _ORIGINAL_PYC.exists():
        raise FileNotFoundError(
            "Legacy bytecode missing. Expected to find "
            f"{_ORIGINAL_PYC} so the UI can be reconstructed."
        )
    loader = importlib.machinery.SourcelessFileLoader(_MODULE_NAME, str(_ORIGINAL_PYC))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


_original_module = _load_original_module()
_reserved_names = set(globals()) | {"_original_namespace"}
_original_namespace = vars(_original_module)

for _name, _value in _original_namespace.items():
    if _name in _reserved_names:
        continue
    if _name.startswith("__") and _name not in {"__all__"}:
        continue
    globals()[_name] = _value

__all__ = getattr(_original_module, "__all__", None)
if __all__ is None:
    __all__ = [n for n in _original_namespace.keys() if not n.startswith("_")]

messagebox = globals().get("messagebox", _tk_messagebox)
logger = globals().get("logger")
if logger is None:
    logger = logging.getLogger("FYIUploaderApp")

facebook_uploader = globals().get("facebook_uploader")
if facebook_uploader is None:
    facebook_uploader = __import__("facebook_uploader")

FYIUploaderApp = globals()["FYIUploaderApp"]


_original_init = FYIUploaderApp.__init__


def _patched_app_init(self, *args, **kwargs):
    _original_init(self, *args, **kwargs)
    if not hasattr(self, "_smart_queue_state"):
        self._smart_queue_state = None
    if not hasattr(self, "_smart_queue_job"):
        self._smart_queue_job = None
    if not hasattr(self, "smart_scheduler_queue"):
        self.smart_scheduler_queue = queue.Queue()
    if not hasattr(self, "smart_scheduler_workers"):
        self.smart_scheduler_workers = 2
    if not hasattr(self, "video_queue"):
        self.video_queue = []
    if not hasattr(self, "processed_videos"):
        self.processed_videos = set()
    if not hasattr(self, "upload_status"):
        self.upload_status = {}
    if not hasattr(self, "post_upload_delay"):
        self.post_upload_delay = 2


FYIUploaderApp.__init__ = _patched_app_init


# ---------------------------------------------------------------------------
# Helper overrides
# ---------------------------------------------------------------------------

def _patched_update_upload_status(self, platform, video_path, status_text):
    status_key = self._status_key(platform, video_path)

    def _apply():
        self.upload_status[status_key] = status_text
        self._refresh_queue_display(platform)

    if threading.current_thread() is threading.main_thread():
        _apply()
    else:
        self.after(0, _apply)


def _patched_status_key(self, platform, video_path):
    return f"{platform}_{video_path}"


def _patched_format_duration(self, seconds: float) -> str:
    seconds = max(0, int(seconds))
    mins, secs = divmod(seconds, 60)
    hours, mins = divmod(mins, 60)
    if hours:
        return f"{hours}h {mins}m {secs:02d}s"
    if mins:
        return f"{mins}m {secs:02d}s"
    return f"{secs}s"


def _patched_get_pending_videos(self, platform: str) -> List[str]:
    pending: List[str] = []
    for video_path in self.video_queue:
        status_key = self._status_key(platform, video_path)
        status = self.upload_status.get(status_key, "") or "Waiting"
        if any(flag in status for flag in ("Waiting", "Queued", "Failed")):
            pending.append(video_path)
    return pending


def _patched_mark_for_retry(self, video_path: str):
    if video_path in self.processed_videos:
        self.processed_videos.discard(video_path)
        self.update_count_label()


def _patched_update_count_label(self):
    def _apply():
        video_queue = getattr(self, "video_queue", [])
        processed = len(getattr(self, "processed_videos", []))
        total = getattr(self, "total_videos", 0) or len(video_queue)

        if not total and not video_queue:
            self.queue_label.configure(text="Queue: Empty")
            return

        total = max(total, len(video_queue))
        processed = max(0, min(processed, total))
        self.queue_label.configure(text=f"Queue: ({processed}/{total})")

    if threading.current_thread() is threading.main_thread():
        _apply()
    else:
        self.after(0, _apply)


def _patched_drain_smart_queue(self):
    state = getattr(self, "_smart_queue_state", None)
    if not state:
        self._smart_queue_job = None
        return

    progress_queue = state.get("queue")
    platform = state.get("platform", "Facebook")
    updated = False

    while True:
        try:
            event = progress_queue.get_nowait()
        except queue.Empty:
            break

        updated = True
        event_type = event.get("type")

        if event_type == "start":
            video_path = event["video"]
            idx = event["idx"]
            total = event["total"]
            self._update_upload_status(platform, video_path, f"Starting ({idx}/{total})")
        elif event_type == "progress":
            video_path = event["video"]
            message = event.get("message", "Uploading...")
            self._update_upload_status(platform, video_path, message)
        elif event_type == "done":
            video_path = event["video"]
            idx = event["idx"]
            total = event["total"]
            ok = event.get("ok", False)
            message = event.get("message", "")
            display_time = event.get("display_time", "")
            elapsed = event.get("elapsed", 0.0)
            duration = self._format_duration(elapsed)
            state["completed"] = state.get("completed", 0) + 1

            if ok:
                self.processed_videos.add(video_path)
                self.log_successful_upload(Path(video_path).name, display_time)
                self.update_count_label()
                self._update_upload_status(
                    platform,
                    video_path,
                    f"Scheduled {display_time} • {duration}",
                )
                status_msg = (
                    f"SMART SCHEDULE ({idx}/{total}): "
                    f"{Path(video_path).name} → {display_time}"
                )
                self.status_label.configure(text=status_msg, text_color="#4CAF50")
            else:
                self._update_upload_status(platform, video_path, f"Failed: {message}")
                self.status_label.configure(text=f"Failed: {message}", text_color="#FF6B6B")
                logger.error(f"SMART FAILED: {Path(video_path).name} :: {message}")
        elif event_type == "all_done":
            state["running"] = False

    if state.get("running", False):
        self._smart_queue_job = self.after(150, self._drain_smart_queue)
    else:
        total = state.get("total", 0)
        completed = state.get("completed", 0)
        elapsed = time.perf_counter() - state.get("start", time.perf_counter())
        duration = self._format_duration(elapsed)
        summary = f"Smart Scheduler finished ({completed}/{total}) in {duration}"
        if completed == total:
            self.status_label.configure(text=summary, text_color="#4CAF50")
        else:
            self.status_label.configure(text=summary, text_color="#FF8800")
        self._smart_queue_state = None
        self._smart_queue_job = None

    if not updated and self._smart_queue_job is None:
        # Nothing to process and not rescheduled – ensure state cleared
        self._smart_queue_state = None
        self.update_count_label()


# ---------------------------------------------------------------------------
# Scheduler overrides
# ---------------------------------------------------------------------------

def _patched_fb_scheduler(self, platform):
    if not self.video_queue:
        self.status_label.configure(text="Queue empty.", text_color="#FF6B6B")
        return
    account, error = self._get_selected_account(platform)
    if not account:
        self.status_label.configure(text=error, text_color="#FF6B6B")
        return
    self.planner_opened = False
    if self.refresh_timer:
        self.after_cancel(self.refresh_timer)
        self.refresh_timer = None
    interval = self.scheduler_interval_minutes
    specific = self.scheduler_specific_dt
    self.status_label.configure(text="Scheduling on Facebook...", text_color="#1877F2")

    pending_videos = self._get_pending_videos(platform)
    if not pending_videos:
        self.status_label.configure(text="All videos already scheduled.", text_color="#4CAF50")
        return

    def run():
        nonlocal specific
        page_id = getattr(account, "page_id", None)
        token = getattr(account, "access_token", None)
        use_specific = specific
        total = len(pending_videos)
        for idx, vid_path in enumerate(pending_videos, start=1):
            vid = Path(vid_path)
            captioned = self._compose_caption_text(vid.stem)
            title = desc = captioned
            file_size = vid.stat().st_size
            if use_specific:
                sched_dt = use_specific
                use_specific = None
            else:
                sched_dt = datetime.now() + timedelta(minutes=interval)
            sched_ts = self.get_valid_schedule_time(sched_dt)
            scheduled_time = datetime.fromtimestamp(sched_ts).strftime("%I:%M %p")
            self._mark_for_retry(vid_path)
            self._update_upload_status("Facebook", vid_path, f"Queued → {scheduled_time}")
            start_ts = time.perf_counter()

            def cb(msg):
                if "Uploading" in msg:
                    try:
                        uploaded = int(msg.split()[1])
                        pct = min(99, int((uploaded / file_size) * 100))
                        self.status_label.configure(
                            text=f"Scheduler {idx}/{total}: {pct}%",
                            text_color="#1877F2"
                        )
                        logger.info(f"FB UPLOAD: {vid.name} → {pct}%")
                        self._update_upload_status("Facebook", vid_path, f"{pct}%")
                    except Exception:
                        self.status_label.configure(text="Uploading...", text_color="#1877F2")
                else:
                    logger.info(f"FB API: {msg}")

            logger.info(f"FB UPLOAD: Starting {vid.name} @ {scheduled_time}")
            ok, msg, _ = facebook_uploader.upload_video_to_facebook(
                str(vid), title, desc, cb, sched_ts, page_id=page_id, access_token=token
            )
            elapsed = time.perf_counter() - start_ts
            if ok:
                self.log_successful_upload(vid.name, scheduled_time)
                self.processed_videos.add(vid_path)
                self.update_count_label()
                duration_text = self._format_duration(elapsed)
                self.status_label.configure(
                    text=(
                        f"UPLOADED & SCHEDULED ({idx}/{total}): "
                        f"{vid.name} → {scheduled_time} ({duration_text})"
                    ),
                    text_color="#4CAF50"
                )
                self._update_upload_status(
                    "Facebook", vid_path, f"Scheduled {scheduled_time} • {duration_text}"
                )
                logger.info(f"FB SUCCESS: Scheduled {vid.name} at {scheduled_time}")
            else:
                self.status_label.configure(text=f"Failed: {vid.name}", text_color="#FF6B6B")
                self._update_upload_status("Facebook", vid_path, "Failed")
                logger.error(f"FB FAILED: {msg}")
                self.processed_videos.add(vid_path)
                self.update_count_label()
            time.sleep(self.post_upload_delay)
        self.status_label.configure(text="ALL VIDEOS SCHEDULED!", text_color="#4CAF50")

    threading.Thread(target=run, daemon=True).start()


def _patched_smart_scheduler(self, platform):
    if not self.video_queue:
        self.status_label.configure(text="Select videos first", text_color="#FF6B6B")
        return
    if self._smart_queue_state:
        self.status_label.configure(text="Smart Scheduler already running...", text_color="#FF8800")
        return
    account, error = self._get_selected_account(platform)
    if not account:
        self.status_label.configure(text=error, text_color="#FF6B6B")
        return
    interval = self.scheduler_interval_minutes
    if interval < 1 and self.scheduler_specific_dt is None:
        messagebox.showerror("Error", "Set interval in Scheduler Settings first")
        return

    pending_videos = self._get_pending_videos(platform)
    if not pending_videos:
        self.status_label.configure(text="All videos already scheduled.", text_color="#4CAF50")
        return

    self.status_label.configure(text="Analyzing page schedule...", text_color="#8E44AD")
    page_id = getattr(account, "page_id", None)
    token = getattr(account, "access_token", None)

    scheduled = facebook_uploader.get_scheduled_videos(page_id, token)
    if scheduled:
        times = [v.get("scheduled_publish_time") for v in scheduled if v.get("scheduled_publish_time")]
        last = datetime.fromtimestamp(max(times)) if times else datetime.now()
        logger.info(
            f"SMART: Found {len(scheduled)} scheduled videos – latest at {last.strftime('%I:%M %p')}"
        )
    else:
        cached = facebook_uploader.get_last_scheduled_time(page_id)
        if cached:
            last = datetime.fromtimestamp(int(cached))
            logger.info(
                f"SMART: Using cached last scheduled time for page {page_id} -> {last.strftime('%I:%M %p')}"
            )
        else:
            last = datetime.now()
            logger.info("SMART: No scheduled videos – start now.")

    tasks = []
    total = len(pending_videos)
    for idx, vid_path in enumerate(pending_videos, start=1):
        vid = Path(vid_path)
        captioned = self._compose_caption_text(vid.stem)
        if self.scheduler_specific_dt:
            sched_dt = self.scheduler_specific_dt
        else:
            sched_dt = max(last + timedelta(minutes=interval), datetime.now() + timedelta(minutes=10))
        sched_ts = self.get_valid_schedule_time(sched_dt)
        scheduled_time = datetime.fromtimestamp(sched_ts).strftime("%I:%M %p")
        last = datetime.fromtimestamp(sched_ts)
        self._mark_for_retry(vid_path)
        self._update_upload_status(platform, vid_path, f"Queued → {scheduled_time}")
        tasks.append({
            "idx": idx,
            "total": total,
            "video": vid_path,
            "title": captioned,
            "description": captioned,
            "ts": sched_ts,
            "display_time": scheduled_time,
            "page_id": page_id,
            "token": token,
        })

    if not tasks:
        self.status_label.configure(text="No pending videos to schedule.", text_color="#FF8800")
        return

    progress_queue = queue.Queue()
    self._smart_queue_state = {
        "queue": progress_queue,
        "platform": platform,
        "total": len(tasks),
        "completed": 0,
        "start": time.perf_counter(),
        "running": True,
    }
    self._smart_queue_job = self.after(150, self._drain_smart_queue)

    workers = min(self.smart_scheduler_workers, len(tasks)) or 1
    self.status_label.configure(
        text=f"Smart Scheduler running ({workers} parallel uploads)...",
        text_color="#8E44AD",
    )

    def worker(task):
        video_path = task["video"]
        idx = task["idx"]
        total_local = task["total"]
        display_time = task["display_time"]
        start_ts = time.perf_counter()

        progress_queue.put({
            "type": "start",
            "platform": platform,
            "video": video_path,
            "idx": idx,
            "total": total_local,
        })

        def cb(message):
            progress_queue.put({
                "type": "progress",
                "platform": platform,
                "video": video_path,
                "idx": idx,
                "total": total_local,
                "message": message,
            })

        try:
            ok, msg, _ = facebook_uploader.upload_video_to_facebook(
                video_path,
                task["title"],
                task["description"],
                cb,
                task["ts"],
                page_id=task["page_id"],
                access_token=task["token"],
            )
        except Exception as exc:  # noqa: BLE001 - propagate user-facing error
            ok, msg = False, str(exc)

        elapsed = time.perf_counter() - start_ts
        progress_queue.put({
            "type": "done",
            "platform": platform,
            "video": video_path,
            "idx": idx,
            "total": total_local,
            "ok": ok,
            "message": msg,
            "display_time": display_time,
            "elapsed": elapsed,
        })
        if self.post_upload_delay:
            time.sleep(self.post_upload_delay)

    def runner():
        with ThreadPoolExecutor(max_workers=workers) as executor:
            for task in tasks:
                executor.submit(worker, task)
        progress_queue.put({"type": "all_done"})

    threading.Thread(target=runner, daemon=True).start()


def _install_scheduler_patches():
    target = FYIUploaderApp
    target._update_upload_status = _patched_update_upload_status
    target._status_key = _patched_status_key
    target._format_duration = _patched_format_duration
    target._get_pending_videos = _patched_get_pending_videos
    target._mark_for_retry = _patched_mark_for_retry
    target.update_count_label = _patched_update_count_label
    target._drain_smart_queue = _patched_drain_smart_queue
    target.fb_scheduler = _patched_fb_scheduler
    target.smart_scheduler = _patched_smart_scheduler


_install_scheduler_patches()


if __name__ == "__main__":
    app = FYIUploaderApp()
    logger.info("FYI Uploader started with patched scheduler")
    app.mainloop()
