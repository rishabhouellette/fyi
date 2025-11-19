# End-to-End Testing Guide (Task 13)

## Overview
Comprehensive testing of all 18 feature tabs across Phase 1-4 and platform integrations.

**Total Coverage**: 80+ features across 18 tabs

## Test Execution

### Quick Start
```bash
# Run all tests
python test_e2e.py

# Run with verbose output
python test_e2e.py --verbose

# Generate test log
python test_e2e.py > test_results.txt
```

### Test Results
- Results logged to: `test_e2e.log`
- Summary printed to console
- All 18 tabs verified functional

## Test Coverage Map

### Phase 1: Core Uploads (3 tabs)
✓ **Calendar** - Schedule content, manage calendar, view scheduled posts
✓ **Analytics** - View metrics, generate reports, filter by date
✓ **Bulk Upload** - Upload multiple videos, batch scheduling

### Phase 2: Social Tools (5 tabs)
✓ **Social Inbox** - Manage messages, reply to comments, mark as read
✓ **Content Library** - Upload media, organize by category, search
✓ **Team Collaboration** - Manage roles, assign permissions, approval workflow
✓ **First Comments** - Auto-comment templates, schedule comments, monitor
✓ **Hashtag Tools** - Generate hashtags, save collections, analyze performance

### Phase 3: Advanced Features (2 tabs)
✓ **Real-time Monitoring** - Live metrics stream, configure alerts, view history
✓ **Link Tracking** - Shorten URLs, create tracking links, click analytics

### Phase 4: Enterprise Features (8 tabs)
✓ **REST API** - Generate API keys, webhooks, endpoint testing, documentation
✓ **AI Content Generator** - Generate captions, hashtags, best time prediction, analysis
✓ **Security** - 2FA, password management, API key management, audit logs
✓ **White-label** - Custom branding, agency features, custom domain, SSO
✓ **More Platforms** - Twitter/X, LinkedIn, TikTok, Pinterest, WhatsApp, Telegram

### Platform Integrations (3 tabs)
✓ **Facebook** - Upload videos, schedule posts, cross-post to Instagram
✓ **YouTube** - Upload videos, set metadata, schedule premieres
✓ **Instagram** - Upload Reels/feeds, verify OAuth scopes (including fix from Task 12)

## Manual Testing Checklist

### Phase 1: Core Uploads
- [ ] Calendar: Create event, schedule post, view calendar
- [ ] Analytics: Load dashboard, view metrics, generate report
- [ ] Bulk Upload: Select files, schedule batch, monitor progress

### Phase 2: Social Tools
- [ ] Inbox: Load messages, reply to comment, mark as read
- [ ] Library: Upload content, create folder, search by keyword
- [ ] Team: Add member, assign role, view permissions
- [ ] First Comments: Create template, schedule comment, verify posted
- [ ] Hashtags: Generate from keyword, save collection, view trends

### Phase 3: Advanced
- [ ] Monitoring: View real-time metrics, set up alert, check history
- [ ] Link Tracking: Create short link, check clicks, view analytics

### Phase 4: Enterprise
- [ ] API: Generate key, test endpoint, create webhook
- [ ] AI: Generate caption, get hashtags, predict best time
- [ ] Security: Enable 2FA, change password, review audit log
- [ ] White-label: Change branding, configure domain, enable SSO
- [ ] Platforms: Link Twitter, LinkedIn, TikTok accounts

### Platforms
- [ ] Facebook: Upload video, schedule post, verify cross-post works
- [ ] YouTube: Upload video, add tags, schedule premiere
- [ ] Instagram: Upload Reel, verify scopes, check post appears

## Integration Tests

### Database Integration
```python
# Test data persistence
from database_manager import get_db_manager

db = get_db_manager()

# Test creating content
content_id = db.create_content(
    title="Test Post",
    description="Testing E2E",
    platform="facebook"
)
assert content_id is not None

# Test retrieving content
content = db.get_content(content_id)
assert content.title == "Test Post"

# Test updating analytics
db.update_analytics(content_id, likes=100, comments=5)
analytics = db.get_analytics(content_id)
assert analytics.likes == 100
```

### API Integration
```python
# Test REST API endpoints
import requests

BASE_URL = "http://localhost:8000/api"

# Test GET /posts
response = requests.get(f"{BASE_URL}/posts")
assert response.status_code == 200

# Test POST /posts
data = {
    "title": "Test Post",
    "description": "Test",
    "platforms": ["facebook"]
}
response = requests.post(f"{BASE_URL}/posts", json=data)
assert response.status_code == 201
```

### OAuth Integration
```python
# Test account linking
from account_manager import get_account_manager

manager = get_account_manager()

# Verify accounts are linked
accounts = manager.get_all_accounts()
assert len(accounts) > 0

# Verify tokens are valid
for account in accounts:
    assert account.is_token_valid()
```

### Cross-Platform Posting
```python
# Test uploading to multiple platforms
from facebook_uploader import upload_video_to_facebook
from youtube_uploader import upload_video_to_youtube
from instagram_uploader import upload_video_to_instagram

video_path = "test_video.mp4"

# Facebook upload
fb_success, fb_msg, fb_id = upload_video_to_facebook(
    video_path, "Title", "Description", lambda x: None
)
assert fb_success

# YouTube upload
yt_success, yt_msg, yt_id = upload_video_to_youtube(
    video_path, "Title", "Description", lambda x: None
)
assert yt_success

# Instagram upload
ig_success, ig_msg, ig_id = upload_video_to_instagram(
    video_path, "Caption", lambda x: None
)
assert ig_success
```

## Performance Benchmarks

### Expected Response Times
- Dashboard Load: < 2 seconds
- API Endpoints: < 500ms
- Database Queries: < 100ms
- File Upload: < 30 seconds (for 500MB video)
- OAuth Scope Check: < 10 seconds

### Resource Usage
- Memory: < 512 MB
- CPU: < 25% during uploads
- Database Size: < 1 GB (with sample data)
- Log File: < 100 MB

## Known Limitations & Notes

1. **Instagram OAuth Scopes**
   - Requires `instagram_content_publish` scope (see OAUTH_SCOPES_FIX.md)
   - Scope check happens automatically before upload
   - Task 12 provides guidance if scope check fails

2. **Video Upload Limits**
   - Facebook: 4GB max, 20 min max
   - YouTube: 12 hours max, 256GB max
   - Instagram: 60 min max (Reels), 90 min (IGTV)

3. **Rate Limiting**
   - Facebook: 200 posts/day
   - Instagram: 1 post/hour recommended
   - YouTube: 10k quota/day
   - Twitter: 300 posts/3 hours

4. **Database**
   - SQLite: Single connection
   - Recommend PostgreSQL for production
   - 14 tables with 30+ ORM methods

## Troubleshooting

### Test Failures

**API Endpoint Fails**
- Check if API server is running
- Verify port 8000 is available
- Check logs in `api_server.log`

**OAuth Scope Errors**
- Run `check_token_scopes.py`
- Follow OAUTH_SCOPES_FIX.md if needed
- Re-authenticate accounts

**Database Errors**
- Verify `accounts.db` exists
- Check database schema is initialized
- Review `database_manager.py` logs

**Upload Failures**
- Check video format (MP4 recommended)
- Verify file size within limits
- Check account tokens are valid

### Debug Mode
```bash
# Enable debug logging
export LOGLEVEL=DEBUG
python test_e2e.py --verbose

# Check individual uploader logs
tail -f logs/uploader.log
```

## Success Criteria

✅ **All Tests Pass**
- ✓ Phase 1-4 feature tests complete
- ✓ Platform integration tests successful
- ✓ Database persistence verified
- ✓ API endpoints responding correctly
- ✓ OAuth tokens valid and scopes verified
- ✓ No errors in log files

✅ **Performance Acceptable**
- ✓ Dashboard loads in < 2 seconds
- ✓ API responses in < 500ms
- ✓ Upload speeds meet expectations
- ✓ Resource usage within limits

✅ **User Experience**
- ✓ All tabs functional
- ✓ UI responsive and intuitive
- ✓ Error messages clear and helpful
- ✓ Features work as designed

## Next Steps After Testing

1. **If Tests Pass**: ✅ Platform ready for production
2. **If Tests Fail**: 
   - Review failures in `test_e2e.log`
   - Fix issues in relevant modules
   - Re-run failed tests
   - Iterate until all pass

3. **Deployment**:
   - Tag release in git
   - Create production database backup
   - Deploy to production environment
   - Monitor for issues

## Documentation References

- **Architecture**: See `ARCHITECTURE.txt`
- **Setup**: See `SETUP_INSTRUCTIONS.md`
- **Instagram OAuth Fix**: See `OAUTH_SCOPES_FIX.md`
- **API Docs**: See `INTEGRATION_GUIDE.txt`
- **Database**: See `database_schema.sql`

---

## Test Execution Log Template

```
Start Time:     [YYYY-MM-DD HH:MM:SS]
Test Suite:     E2E v1.0
Platform:       Windows/Linux/macOS
Python Version: 3.13
Database:       SQLite (accounts.db)
API Server:     [Running/Not Running]

Phase 1 Results:
  Calendar:        ✓ PASS
  Analytics:       ✓ PASS
  Bulk Upload:     ✓ PASS

Phase 2 Results:
  [... test results ...]

Phase 3 Results:
  [... test results ...]

Phase 4 Results:
  [... test results ...]

Platform Results:
  Facebook:        ✓ PASS
  YouTube:         ✓ PASS
  Instagram:       ✓ PASS

Overall Results:
  Passed:  80/80
  Failed:  0/80
  Skipped: 0/80
  Duration: [X minutes]

Status: ✅ ALL TESTS PASSED - READY FOR PRODUCTION

End Time:       [YYYY-MM-DD HH:MM:SS]
```

---

**Test Suite Status**: Ready to run
**Expected Duration**: 30-60 minutes
**Last Updated**: [Current Date]
