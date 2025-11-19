# scheduler_engine.py
import os, time, threading
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Callable, Optional
from logger_config import get_logger

logger = get_logger(__name__)
LOG = "fyi_queue_log.csv"

class SchedulerEngine:
    def __init__(self):
        self._running = threading.Event()
        self._thread = None
        self.video_queue: List[str] = []
        self.log_cb: Optional[Callable[[str], None]] = None
        self.count_cb: Optional[Callable[[], None]] = None
        self.platform = "Facebook"
        self.interval_minutes = 60
        self.specific_dt = None
        self.failed_videos = set()

    def start(self, q, log, cnt, plat, interval_min=60, specific_dt=None):
        if self._thread and self._thread.is_alive():
            return
        self.video_queue = [v for v in q if v not in self.failed_videos]
        self.log_cb = log
        self.count_cb = cnt
        self.platform = plat
        self.interval_minutes = interval_min
        self.specific_dt = specific_dt
        self._running.set()
        self._thread = threading.Thread(target=self._worker, daemon=True)
        self._thread.start()

    def pause(self): self._running.clear()

    def resume(self): self._running.set()

    def stop(self):
        self._running.clear()
        if self._thread:
            self._thread.join(timeout=1)
        self._thread = None
        self.video_queue.clear()

    def _worker(self):
        logger.info(f"[Scheduler] Started for {self.platform}")
        while self._thread:
            if not self._running.is_set():
                time.sleep(1)
                continue
            if not self.video_queue:
                time.sleep(10)
                continue
            next_time = self._get_next_schedule_time()
            now = datetime.now()
            if next_time <= now:
                logger.info("[Scheduler] Time is past → uploading now")
                next_time = now + timedelta(seconds=10)
            wait_sec = max(0, (next_time - now).total_seconds())
            logger.info(f"[Scheduler] Next video in {int(wait_sec)}s → {next_time.strftime('%H:%M')}")
            time.sleep(wait_sec)
            self._schedule_next()

    def _get_next_schedule_time(self):
        if self.specific_dt:
            return self.specific_dt
        else:
            return datetime.now() + timedelta(minutes=self.interval_minutes)

    def _schedule_next(self):
        vid_path = self.video_queue[0]
        vid = Path(vid_path)
        sched_dt = self._get_next_schedule_time()
        sched_ts = int(sched_dt.timestamp())
        title = vid.stem
        desc = title
        def cb(m): logger.info(f"[Upload] {m}")
        logger.info(f"[Scheduler] Uploading: {vid.name} → {sched_dt.strftime('%Y-%m-%d %H:%M')}")
        ok, msg = False, ""
        try:
            if self.platform == "Facebook":
                from facebook_uploader import upload_video_to_facebook
                ok, msg, _ = upload_video_to_facebook(str(vid), title, desc, cb, sched_ts)
            elif self.platform == "YouTube":
                from youtube_uploader import upload_video_to_youtube
                ok, msg = upload_video_to_youtube(str(vid), title, desc, [], cb, sched_ts)
            elif self.platform == "Instagram":
                from instagram_uploader import upload_video_to_instagram
                ok, msg, _ = upload_video_to_instagram(str(vid), desc, cb)
        except Exception as e:
            ok, msg = False, f"Exception: {e}"
        if ok:
            logger.info("[Scheduler] SUCCESS → Removed")
            self.video_queue.pop(0)
            if self.log_cb: self.log_cb(vid.name)
            if self.count_cb: self.count_cb()
            self._log("SCHEDULED", vid.name, sched_dt.isoformat(), msg)
            if self.specific_dt: self.specific_dt = None
        else:
            logger.warning(f"[Scheduler] FAILED → Skipping: {msg}")
            self.video_queue.pop(0)
            self.failed_videos.add(vid_path)
            self._log("FAILED", vid.name, sched_dt.isoformat(), msg)
            if self.count_cb: self.count_cb()

    def _log(self, st, file, sch, msg):
        p = Path(LOG)
        if not p.exists():
            p.write_text("timestamp,file,status,scheduled_time,message\n", encoding="utf-8")
        with p.open("a", encoding="utf-8") as f:
            f.write(f"{datetime.now().isoformat()},{file},{st},{sch},{msg}\n")

engine = SchedulerEngine()
